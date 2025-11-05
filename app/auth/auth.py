import time
import logging
from datetime import datetime, timezone
from typing import List
import jwt
from pydantic import BaseModel
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import pydantic
from app.config import settings
from app.core.exceptions import CustomHTTPException
from app.core.logger import DEBUG_QUALNAME
from app.core.schemas import unauthorized_response, UnauthorizeCode

_logger = logging.getLogger(DEBUG_QUALNAME)

BEARER_TOKEN_TYPE = "Bearer"

class InvalidIssuer(Exception):
    ...

class ExpiredToken(Exception):
    ...

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenClaims(BaseModel):
    iss: str
    aud: str
    iat: float
    exp: float
    sub: str

# class RoleChecker:
#     """
#     Dependency that checks if the authenticated user has at least one of the required roles.
#     """
#     def __init__(self, allowed_roles: List[str]):
#         self.allowed_roles = allowed_roles

#     def __call__(self, current_user: User = Depends(get_current_user)):
#         if not self.allowed_roles:
#             return  # If no roles are required, allow access.

#         user_roles = set(current_user.roles)
#         if not user_roles.intersection(self.allowed_roles):
#             _logger.warning(
#                 "User does not have required roles",
#                 username=current_user.username,
#                 required_roles=self.allowed_roles,
#             )
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def validate_token(request: Request, token: str= Depends(oauth2_scheme)):
    print("#======= token : ", token)
    if token == settings.API_KEY:
        return token
    claim = decode_jwt_token(token=token)
    if claim.sub == settings.API_USER:
        return token
    raise unauthorized_response(code=UnauthorizeCode.INVALID_JWT, mesg="Invalid authentication credentials : Wrong API Key")

def decode_jwt_token(token: str, **options) -> TokenClaims:
    try:
        return TokenClaims.parse_obj(jwt.decode(
                jwt        = token,
                key        = settings.API_KEY,
                algorithms = settings.API_JWT_ALGORITHM,
                audience   = settings.API_JWT_AUDIENCES,
                issuer     = settings.API_JWT_ISSUER,
                options=options
            ))
    except jwt.exceptions.DecodeError as err:
        raise unauthorized_response(code = UnauthorizeCode.INVALID_JWT, mesg = "Authentication Required") from err
    except jwt.exceptions.ImmatureSignatureError as err:
        raise unauthorized_response(code = UnauthorizeCode.INVALID_IAT, mesg = "Authentication Required") from err
    except jwt.exceptions.ExpiredSignatureError as err:
        raise unauthorized_response(code = UnauthorizeCode.INVALID_EXP, mesg = "Authentication Required") from err
    except jwt.exceptions.InvalidIssuerError as err:
        raise unauthorized_response(code = UnauthorizeCode.INVALID_ISS, mesg = "Authentication Required") from err
    except jwt.exceptions.InvalidAudienceError as err:
        raise unauthorized_response(code = UnauthorizeCode.INVALID_AUD, mesg = "Authentication Required") from err
    except pydantic.ValidationError as err:
        raise unauthorized_response(code = UnauthorizeCode.INVALID_CLM, mesg = "Authentication Required") from err

async def generate_jwt_token(subject: str, issuer: str = settings.API_JWT_ISSUER, audience: str = settings.API_JWT_AUDIENCES) -> Token:
    now_time = datetime.now(tz=timezone.utc).timestamp()
    claim = TokenClaims(
        iss = issuer,
        aud = audience,
        iat = now_time,
        exp = now_time + settings.API_JWT_TOKEN_DURATION,
        sub = subject
    )
    token_str = jwt.encode(claim.dict(), settings.API_KEY, algorithm=settings.API_JWT_ALGORITHM)
    return Token(token_type="Bearer", access_token=token_str)

jwt_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token/jwt/login")

async def validate_jwt_token(request: Request, token: str = Depends(jwt_oauth2_scheme)) -> TokenClaims:
    _logger.debug("#CHK JWT Authentication started : %s", time.time())
    try:
        claim = decode_jwt_token(token=token)
        request.state.user = claim.sub
    except CustomHTTPException as err:
        if hasattr(err.obj, 'status') and err.obj.status == UnauthorizeCode.INVALID_JWT.value and token == settings.API_KEY:
            return token
        raise err
    return token
