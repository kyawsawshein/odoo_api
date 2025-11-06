"""Authentication utilities"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import settings
from app.auth.models.models import TokenData


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    print("#======== password ", plain_password, hashed_password)
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(
    data: TokenData, expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    if expires_delta:
        data.exp = datetime.utcnow() + expires_delta
    else:
        data.exp = datetime.utcnow() + timedelta(
            minutes=settings.API_JWT_TOKEN_DURATION
        )
    encoded_jwt = jwt.encode(
        data.model_dump(), settings.API_KEY, algorithm=settings.API_JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        return TokenData(
            **jwt.decode(
                token, settings.API_KEY, algorithms=[settings.API_JWT_ALGORITHM]
            )
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_token(name: str, user_id: int, scopes: list) -> str:
    """Generate API token for external integrations"""
    data = {"name": name, "user_id": user_id, "scopes": scopes, "type": "api_token"}
    return create_access_token(data, expires_delta=timedelta(days=365))


def validate_api_token(token: str, required_scopes: list = None) -> TokenData:
    """Validate API token and check scopes"""
    token_data = verify_token(token)

    if required_scopes:
        for scope in required_scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope: {scope}",
                )

    return token_data
