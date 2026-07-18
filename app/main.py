from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.router import api_v1_router
from app.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import redis_client
from app.seed import seed_initial_data
from app.modules.rbac.models import Role, Permission # Modellar yaratilishi uchun import
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await seed_initial_data(db)

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

from app.modules.admin.web import router as admin_web_router
app.include_router(admin_web_router)

# Static files va upload papkasini sozlash
UPLOAD_DIR = "static/uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")