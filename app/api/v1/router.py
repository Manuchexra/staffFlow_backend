from fastapi import APIRouter
from app.modules.auth.endpoints import router as auth_router
from app.modules.attendance.endpoints import router as attendance_router
from app.modules.salary.endpoints import router as salary_router
from app.modules.users.endpoints import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(attendance_router)
api_v1_router.include_router(salary_router)
api_v1_router.include_router(users_router)