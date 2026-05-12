from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api.v1.router import api_v1_router
from app.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import redis_client
from app.seed import seed_initial_data
from contextlib import asynccontextmanager
import logging
import time
from fastapi.requests import Request

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await seed_initial_data(db)

    yield

    # Shutdown
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

# ⚡ Performance monitoring middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"🐢 Slow request: {request.method} {request.url.path} - {process_time:.2f}s")
    elif process_time > 0.5:
        logger.info(f"⚠️ Medium request: {request.method} {request.url.path} - {process_time:.2f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.include_router(api_v1_router)

# Static files va upload papkasini sozlash
UPLOAD_DIR = "static/uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")