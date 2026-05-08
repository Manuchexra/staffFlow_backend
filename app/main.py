from fastapi import FastAPI
from app.api.v1.router import api_v1_router
from app.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import redis_client
from app.core.security import hash_password
from app.core.deps import UserRole
from app.modules.users.models import User
from sqlalchemy import select
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ma'lumotlar bazasi jadvallarini yaratish
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Admin foydalanuvchini yaratish (agar mavjud bo'lmasa)
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.phone == "+998901234567")
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                phone="+998901234567",
                email="admin@staffflow.uz",
                full_name="Admin User",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                base_salary=0,
                expected_monthly_hours=160
            )
            db.add(admin)
            await db.commit()
            print("✅ Admin user created automatically!")
        else:
            print("ℹ️ Admin already exists.")
    
    yield
    # 3. Resurslarni tozalash
    await redis_client.close()
    await engine.dispose()

app = FastAPI(title="StaffFlow API", lifespan=lifespan)
app.include_router(api_v1_router)