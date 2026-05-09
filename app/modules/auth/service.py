from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.users.models import User
from app.core.security import verify_password, create_access_token, create_refresh_token, increment_failed_login, is_blocked, blacklist_token
from fastapi import HTTPException, status
from app.core.redis_client import redis_client

class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, identifier: str, password: str):
        if await is_blocked(identifier):
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Too many failed attempts. Try again in 15 minutes.")
        stmt = select(User).where((User.phone == identifier) | (User.email == identifier))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            await increment_failed_login(identifier)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        await redis_client.delete(f"login_fail:{identifier}")
        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        return access, refresh

    @staticmethod
    async def logout(token: str):
        # Access tokenni 60 daqiqaga blacklistga qo'shish
        await blacklist_token(token, 3600)
        return {"detail": "Successfully logged out"}