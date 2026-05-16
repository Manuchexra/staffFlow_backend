from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user
from app.modules.users.models import User
from app.modules.rbac.service import RBACService
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

async def get_current_user_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> set[str]:
    # Admin bo'lsa har doim hamma narsaga ruxsat
    if current_user.role == "admin":
        # Barcha permissionlarni olish o'rniga maxsus flag qaytarish ham mumkin
        # Lekin soddalik uchun permissionlarni qaytaramiz
        return {"*"} 
    
    return await RBACService.get_user_permissions(db, current_user.id)

def require_permission(required_permission: str):
    async def permission_checker(permissions: set[str] = Depends(get_current_user_permissions)):
        if "*" in permissions:
            return True
        if required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_permission}"
            )
        return True
    return permission_checker
