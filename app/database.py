from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Production-optimized async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # ⚡ Disable logging for performance
    pool_size=20,  # Connection pool size
    max_overflow=10,  # Additional connections
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=3600,  # Recycle connections every hour
    echo_pool=False,  # Don't log pool operations
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)
Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session