# """Authentication router for FastAPI"""

# from datetime import timedelta
# from typing import Optional

# import requests
# from fastapi import APIRouter, Depends, HTTPException, Request, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.auth.models.models import OdooUserCredentials, Token, User, UserCreate
# from app.auth.utils import (
#     create_access_token,
#     generate_api_token,
#     get_password_hash,
#     verify_password,
#     verify_token,
# )
# from app.config import settings
# from app.core.database import get_db
# from app.odoo.client import OdooClient

# router = APIRouter()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# async def get_current_user(
#     token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
# ) -> User:
#     """Get current authenticated user using .env credentials"""
#     token_data = verify_token(token)

#     # Verify that the username from token matches APP_USER from .env
#     if token_data.username != settings.APP_USER:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user credentials"
#         )
#     # Create a UserSchema object using credentials from .env
#     user = User(
#         id=token_data.user_id,
#         username=settings.APP_USER,
#         email=f"{settings.APP_USER}@example.com",
#         full_name=settings.APP_USER,
#         is_active=True,
#         odoo_url=settings.ODOO_URL,
#         odoo_database=settings.ODOO_DATABASE,
#         odoo_username=settings.ODOO_USERNAME,
#         odoo_password=settings.ODOO_PASSWORD,
#     )

#     return user


# async def get_current_user_optional(
#     request: Request, db: AsyncSession = Depends(get_db)
# ) -> Optional[User]:
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


# @router.post("/token", response_model=Token)
# async def login_for_access_token(
#     form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
# ):
#     """Login and get access token using .env credentials"""
#     # Verify username matches APP_USER from .env
#     if form_data.username != settings.APP_USER:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Verify password matches APP_PASSWORD from .env
#     if not verify_password(form_data.password, settings.APP_PASSWORD):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Create access token
#     access_token_expires = timedelta(minutes=30)
#     access_token = create_access_token(
#         data={"sub": settings.APP_USER, "user_id": 2},
#         expires_delta=access_token_expires,
#     )
#     return Token(
#         access_token=access_token,
#         token_type="bearer",
#         expires_in=access_token_expires.total_seconds(),
#     )


# # @router.post("/register", response_model=User)
# # async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
# #     """Register new user"""
# #     # Check if username already exists
# #     stmt = select(UserSchema).where(UserSchema.username == user_data.username)
# #     result = await db.execute(stmt)
# #     existing_user = result.scalar_one_or_none()

# #     if existing_user:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail="Username already registered",
# #         )

# #     # Check if email already exists
# #     stmt = select(UserSchema).where(UserSchema.email == user_data.email)
# #     result = await db.execute(stmt)
# #     existing_email = result.scalar_one_or_none()

# #     if existing_email:
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
# #         )

# #     # Create new user
# #     hashed_password = get_password_hash(user_data.password)
# #     db_user = UserSchema(
# #         username=user_data.username,
# #         email=user_data.email,
# #         full_name=user_data.full_name,
# #         hashed_password=hashed_password,
# #         is_active=True,
# #     )

# #     db.add(db_user)
# #     await db.commit()
# #     await db.refresh(db_user)

# #     return db_user


# @router.post("/odoo-login")
# async def odoo_login(
#     credentials: OdooUserCredentials,
#     current_user: User = Depends(get_current_user),
# ):
#     """Authenticate with Odoo and get JWT token"""
#     try:
#         # Create Odoo client and authenticate
#         odoo_client = OdooClient(
#             url=settings.ODOO_URL,
#             db=credentials.odoo_database,
#             username=credentials.odoo_username,
#             password=credentials.odoo_password,
#         )
#         uid = await odoo_client.authenticate()
#         if not uid:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid Odoo credentials",
#             )
#         access_token_expires = timedelta(minutes=30)
#         access_token = create_access_token(
#             data={"sub": credentials.odoo_username, "user_id": uid},
#             expires_delta=access_token_expires,
#         )

#         return {
#             "message": "Odoo authentication successful",
#             "user_id": current_user.id,
#             "jwt_token": access_token,
#             "expires_in": access_token_expires,
#             "odoo_user_id": uid,
#             "odoo_username": credentials.odoo_username,
#         }
#         # Call Odoo module to generate JWT token
#         # odoo_jwt_url = f"{settings.ODOO_URL.rstrip('/')}/api/v1/auth/jwt/generate-token"
#         # response = requests.post(
#         #     odoo_jwt_url,
#         #     json={
#         #         "username": credentials.odoo_username,
#         #         "password": credentials.odoo_password,
#         #     },
#         #     timeout=30,
#         # )
#         # print("#===== respnse ", response.status_code)
#         # if response.status_code == 200:
#         #     token_data = response.json()
#         #     if token_data.get("success"):
#         #         return {
#         #             "message": "Odoo authentication successful",
#         #             "odoo_uid": uid,
#         #             "user_id": current_user.id,
#         #             "jwt_token": token_data["data"]["access_token"],
#         #             "token_type": token_data["data"]["token_type"],
#         #             "expires_in": token_data["data"]["expires_in"],
#         #             "odoo_user_id": token_data["data"]["user_id"],
#         #             "odoo_username": token_data["data"]["username"],
#         #             "odoo_user_name": token_data["data"]["name"],
#         #         }
#         #     else:
#         #         raise HTTPException(
#         #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #             detail=f"JWT token generation failed: {token_data.get('error', 'Unknown error')}",
#         #         )
#         # else:
#         #     raise HTTPException(
#         #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         #         detail=f"Failed to call Odoo JWT endpoint: {response.status_code} - {response.text}",
#         #     )

#     except requests.exceptions.RequestException as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Connection to Odoo failed: {str(e)}",
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Odoo authentication failed: {str(e)}",
#         )


# @router.get("/me", response_model=User)
# async def read_users_me(current_user: User = Depends(get_current_user)):
#     """Get current user information"""
#     return current_user


# @router.post("/api-token")
# async def create_api_token(
#     name: str, scopes: list[str], current_user: User = Depends(get_current_user)
# ):
#     """Create API token for external integrations"""
#     api_token = generate_api_token(name, current_user.id, scopes)

#     return {
#         "name": name,
#         "token": api_token,
#         "scopes": scopes,
#         "user_id": current_user.id,
#     }
