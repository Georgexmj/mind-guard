from typing import Callable, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole


def require_role(*roles: UserRole) -> Callable:
    """
    Factory that returns a FastAPI dependency which checks the current user's role.

    Usage:
        @router.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_role(UserRole.admin))):
            ...
    """
    allowed_roles: List[UserRole] = list(roles)

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return current_user
