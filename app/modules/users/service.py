from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.core.security import hash_password
from fastapi import HTTPException, status

class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        # Check if email/phone already exists
        stmt = select(User).where((User.email == user_data.email) | (User.phone == user_data.phone))
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone already registered")
        
        new_user = User(
            email=user_data.email,
            phone=user_data.phone,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            work_start_time=user_data.work_start_time,
            work_end_time=user_data.work_end_time,
            base_salary=user_data.base_salary,
            expected_monthly_hours=user_data.expected_monthly_hours
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def get_all_users(db: AsyncSession):
        stmt = select(User).order_by(User.id)
        result = await db.execute(stmt)
        return result.scalars().all()
