import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

# Ichkaridan (Docker) ulanish uchun DATABASE_URL dan foydalanish
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres123@localhost:5432/staffflow"

async def check_and_fix_schema():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Checking users table schema...")
        
        # avatar_url borligini tekshirish
        result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'avatar_url'"))
        col = result.fetchone()
        
        if not col:
            print("Adding avatar_url column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url TEXT"))
            print("✅ avatar_url column added.")
        else:
            print(f"avatar_url exists with type {col[1]}. Converting to TEXT just in case...")
            await conn.execute(text("ALTER TABLE users ALTER COLUMN avatar_url TYPE TEXT"))
            print("✅ avatar_url converted to TEXT.")

        # position borligini tekshirish
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'position'"))
        if not result.fetchone():
            print("Adding position column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN position VARCHAR(100)"))
            print("✅ position column added.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_and_fix_schema())
