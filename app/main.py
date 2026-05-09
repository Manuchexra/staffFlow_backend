from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router
from app.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import redis_client
from app.seed import seed_initial_data   # import
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await seed_initial_data(db)   # <-- barcha seedlarni ishga tushiradi

    yield

    await redis_client.close()
    await engine.dispose()

app = FastAPI(title="StaffFlow API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)