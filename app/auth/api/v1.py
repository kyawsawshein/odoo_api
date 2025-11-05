"""Authentication router for FastAPI"""

from datetime import timedelta
from typing import Optional
import structlog
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from app.auth.api.route_name import Route
from app.auth.auth import validate_token, generate_jwt_token
from app.auth.authz import get_authz_token
from app.auth.models.models import (
    OdooJWTLoginCredentials,
    OdooUserCredentials,
    Token,
    User,
)
from app.auth.utils import (
    create_access_token,
    generate_api_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.config import settings
from app.core.database import get_db
from app.odoo.client import OdooClient
logger = structlog.get_logger()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current authenticated user.
    Decodes the JWT and populates a User object with Odoo credentials
    stored within the token's claims.
    """
    try:
        token_data = verify_token(token)
        logger.info("Token verified for user", username=token_data.username)
        
        # The token payload must contain the necessary Odoo credentials.
        if not all([token_data.odoo_username, token_data.odoo_password, token_data.odoo_database]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incomplete Odoo credentials in token",
            )

        # Create a User object representing the authenticated user and their Odoo identity.
        user = User(
            id=token_data.user_id,
            username=token_data.username,
            email=f"{token_data.username}@example.com", # Or get from token if available
            full_name=token_data.username,
            is_active=True,
            odoo_url=settings.ODOO_URL, # The Odoo URL is from server settings
            odoo_database=token_data.odoo_database,
            odoo_username=token_data.odoo_username,
            odoo_password=token_data.odoo_password,
            roles=token_data.roles,
        )
        return user
    except HTTPException as e:
        logger.error("Authentication error in get_current_user", detail=e.detail)
        raise e


# async def get_current_user_optional(request: Request) -> Optional[User]:
#     """Get current user if authenticated, otherwise return None"""
#     try:
#         # Extract token from Authorization header
#         auth_header = request.headers.get("Authorization")
#         if not auth_header or not auth_header.startswith("Bearer "):
#             return None

#         token = auth_header.replace("Bearer ", "")
#         token_data = verify_token(token)

#         # Query user from database
#         user = get_current_user()
#         if user is None or not user.is_active:
#             return None

#         return user
#     except Exception:
#         # If any error occurs (invalid token, expired, etc.), return None
#         return None

@router.post(Route.token, response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token using .env credentials"""
    # Verify username matches APP_USER from .env
    if form_data.username != settings.APP_USER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password matches APP_PASSWORD from .env
    # if not verify_password(form_data.password, settings.APP_PASSWORD):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect password",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    if form_data.password != settings.APP_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    return await generate_jwt_token(
            subject=form_data.username, audience=form_data.client_id
        )

@router.post(Route.odoo_login)
async def odoo_login(
    credentials: OdooUserCredentials,
    current_user: User = Depends(get_current_user),
):
    """Authenticate with Odoo and get JWT token"""
    try:
        # Create Odoo client and authenticate
        logger.info("Attempting Odoo login", username=credentials.odoo_username, db=credentials.odoo_database)
        odoo_client = OdooClient(
            url=settings.ODOO_URL,
            db=credentials.odoo_database,
            username=credentials.odoo_username,
            password=credentials.odoo_password,
        )
        uid = await odoo_client.authenticate()
        
        if not uid:
            logger.warning("Invalid Odoo credentials provided", username=credentials.odoo_username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Odoo credentials",
            )
        
        # Fetch user's groups (roles) from Odoo
        user_data = await odoo_client.read_record(
            model="res.users",
            record_id=uid,
            fields=["groups_id"],
        )
        group_ids = user_data.get("groups_id", [])
        
        user_roles = []
        if group_ids:
            groups = await odoo_client.read_records(
                model="res.groups", record_ids=group_ids, fields=["name"]
            )
            user_roles = [group["name"] for group in groups]

        logger.info("Odoo authentication successful", uid=uid, roles=user_roles)
        access_token_expires = timedelta(minutes=30)
        
        # Create a JWT that includes the Odoo credentials for later use.
        access_token = create_access_token(
            data={"sub": credentials.odoo_username, "user_id": uid,
                  "odoo_username": credentials.odoo_username, "odoo_password": credentials.odoo_password, "odoo_database": credentials.odoo_database,
                  "roles": user_roles},
            expires_delta=access_token_expires,
        )

        return {
            "message": "Odoo authentication successful",
            "user_id": current_user.id,
            "jwt_token": access_token,
            "expires_in": access_token_expires,
            "odoo_user_id": uid,
            "odoo_username": credentials.odoo_username,
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection to Odoo failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Odoo authentication failed: {str(e)}",
        )


@router.get(Route.me, response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post(Route.odoo_jwt_login)
async def odoo_jwt_login(
    credentials: OdooJWTLoginCredentials,
    response: Response,
):
    """Authenticate with Odoo JWT endpoint and store token in cookie"""
    try:
        # Extract JWT token from response
        jwt_data = await get_authz_token(
            login=credentials.login, pwd=credentials.password
        )
        jwt_token = jwt_data.get("token")

        if not jwt_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token received from Odoo JWT endpoint",
            )

        # Store JWT token in cookie
        response.set_cookie(
            key="odoo_jwt_token",
            value=jwt_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=24 * 60 * 60,  # 24 hours
        )
        return {
            "message": "Odoo JWT authentication successful",
            "login": credentials.login,
            "token_received": True,
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection to Odoo JWT endpoint failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Odoo JWT authentication failed: {str(e)}",
        )


@router.post(Route.api_token)
async def create_api_token(
    name: str, scopes: list[str], current_user: User = Depends(get_current_user)
):
    """Create API token for external integrations"""
    api_token = generate_api_token(name, current_user.id, scopes)

    return {
        "name": name,
        "token": api_token,
        "scopes": scopes,
        "user_id": current_user.id,
    }
