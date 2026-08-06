# backend/app/auth.py (Addendum)
from fastapi import Depends, HTTPException, status
from .models import User, UserRole

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Ensures the authenticated user has explicit Admin privileges."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Executive Admin privileges required."
        )
    return user
