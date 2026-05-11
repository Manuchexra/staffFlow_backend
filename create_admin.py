import asyncio
import sys
import os

# Add the current directory to sys.path so app can be imported
sys.path.append(os.getcwd())

from app.database import engine, AsyncSessionLocal
from app.modules.users.models import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        email = "admin@gmail.com"
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User {email} already exists. Updating to Admin.")
            user.role = UserRole.ADMIN
            user.hashed_password = hash_password("admin123")
            user.is_active = True
        else:
            print(f"Creating new Admin user: {email}")
            user = User(
                email=email,
                phone="+998901234567",
                first_name="Admin",
                last_name="User",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(user)
        
        await db.commit()
        print("Successfully created/updated admin user.")

if __name__ == "__main__":
    asyncio.run(create_admin())
