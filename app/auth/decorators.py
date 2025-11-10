# from functools import wraps
# from typing import Callable, List

# from fastapi import Depends, HTTPException, status

# from app.auth.api.v1 import get_current_user
# from app.auth.models.models import User


# def require_roles(*required_roles: str):
#     """
#     A decorator to enforce role-based access control on a FastAPI endpoint.

#     It checks if the authenticated user has at least one of the required roles.
#     If the user does not have the required roles, it raises a 403 Forbidden HTTPException.

#     Usage:
#         @router.post("/some/path")
#         @require_roles("Admin", "Project / Manager")
#         async def protected_endpoint(current_user: User = Depends(get_current_user)):
#             ...
#     """

#     def decorator(func: Callable):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             # The `current_user` is expected to be injected by FastAPI into the decorated function's kwargs.
#             user: User = kwargs.get("current_user")
#             if not user:
#                 # This can happen if the dependency is not correctly defined on the endpoint.
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="User not found in request, ensure get_current_user dependency is used.",
#                 )

#             user_roles = set(user.roles)
#             if not user_roles.intersection(required_roles):
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail=f"User lacks required roles. Needs one of: {', '.join(required_roles)}",
#                 )
#             return await func(*args, **kwargs)

#         return wrapper

#     return decorator
