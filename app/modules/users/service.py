from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from fastapi import HTTPException, status, UploadFile
import os
import uuid
import shutil

class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
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
            expected_monthly_hours=user_data.expected_monthly_hours,
            avatar_url=user_data.avatar_url,
            position=user_data.position
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

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, update_data: UserUpdate) -> User:
        user = await UserService.get_user_by_id(db, user_id)
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def change_password(db: AsyncSession, user_id: int, old_password: str, new_password: str) -> bool:
        user = await UserService.get_user_by_id(db, user_id)
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        user.hashed_password = hash_password(new_password)
        await db.commit()
        return True

    @staticmethod
    async def update_avatar(db: AsyncSession, user_id: int, file: UploadFile) -> str:
        # Fayl formatini tekshirish
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Faqat rasm formatidagi fayllar mumkin (.jpg, .png, .webp)")
        
        # Papka mavjudligini ta'minlash
        upload_dir = "static/uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Unique fayl nomi yaratish
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # Faylni saqlash
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # URL yaratish
        avatar_url = f"/static/uploads/avatars/{filename}"
        
        # Bazani yangilash
        user = await UserService.get_user_by_id(db, user_id)
        
        # Agar eski avatar bo'lsa, uni o'chirish (ixtiyoriy, lekin yaxshi)
        if user.avatar_url and user.avatar_url.startswith("/static/"):
            old_path = user.avatar_url.lstrip("/")
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        user.avatar_url = avatar_url
        await db.commit()
        return avatar_url