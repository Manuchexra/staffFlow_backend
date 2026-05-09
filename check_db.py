import asyncio
from app.database import AsyncSessionLocal
from app.modules.users.models import User
from sqlalchemy import select

async def check_user():
    async with AsyncSessionLocal() as db:
        email = "admin@gmail.com"
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            print(f"FOUND: ID={user.id}, Email={user.email}, Phone={user.phone}, Role={user.role}, IsActive={user.is_active}")
        else:
            print(f"NOT FOUND: {email}")

if __name__ == "__main__":
    asyncio.run(check_user())
