from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role, get_current_user
from app.modules.users.models import UserRole, User
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import (
    AdminDashboardResponse,
    HRDashboardResponse,
    EmployeeDashboardResponse
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/admin", response_model=AdminDashboardResponse, summary="[Admin] Asosiy admin dashboard ko'rsatkichlari")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Tizim bo'yicha barcha yuqori darajadagi statistika va ko'rsatkichlar.
    Faqat Administratorlar uchun ochiq.
    """
    return await DashboardService.get_admin_dashboard(db)

@router.get("/hr", response_model=HRDashboardResponse, summary="[HR] HR manager dashboard ko'rsatkichlari")
async def get_hr_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.HR_MANAGER, UserRole.ADMIN]))
):
    """
    Davomat tahlili, kechikishlar, eng yaxshi xodimlar va bugungi ish rejasi.
    HR menejerlar va Adminlar uchun ochiq.
    """
    return await DashboardService.get_hr_dashboard(db)

@router.get("/employee", response_model=EmployeeDashboardResponse, summary="[Employee] Xodim shaxsiy dashboard ko'rsatkichlari")
async def get_employee_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xodimning shaxsiy ish tartibi, bugungi davomati, oylik hisobotlari va bildirishnomalari.
    Barcha tizimga kirgan foydalanuvchilar o'z ma'lumotlarini ko'rishi mumkin.
    """
    return await DashboardService.get_employee_dashboard(db, current_user)
