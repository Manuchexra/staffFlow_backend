from fastapi import Depends, HTTPException, status
from typing import Union
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_token, is_token_blacklisted
from app.modules.users.models import User, UserRole

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or await is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or logged out")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_role(required_roles: Union[UserRole, list[UserRole]]):
    if isinstance(required_roles, UserRole):
        required_roles = [required_roles]

    def role_checker(current_user: User = Depends(get_current_user)):
        # Admin har doim hamma narsaga ruxsat oladi
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Agar talab qilingan rollardan biri bo'lsa
        if current_user.role in required_roles:
            return current_user
            
        # Ierarxiya: HR_MANAGER xodimlar ko'ra oladigan hamma narsani ko'ra olishi kerak
        if UserRole.EMPLOYEE in required_roles and current_user.role == UserRole.HR_MANAGER:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Insufficient permissions. Required: {[r.value for r in required_roles]}"
        )
    return role_checker