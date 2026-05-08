from fastapi import FastAPI
from app.api.v1.router import api_v1_router
from app.database import engine, Base
from app.core.redis_client import redis_client
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await redis_client.close()
    await engine.dispose()

app = FastAPI(title="StaffFlow API", lifespan=lifespan)
app.include_router(api_v1_router)