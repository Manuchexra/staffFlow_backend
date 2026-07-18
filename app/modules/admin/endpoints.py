from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import require_role, UserRole
from app.modules.admin.schemas import AdminDashboardResponse
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService
from app.modules.rbac.schemas import RoleResponse, PermissionResponse
from app.modules.rbac.service import RBACService
from app.modules.reports.service import ReportService

router = APIRouter(prefix="/admin", tags=["Admin Panel"])
admin_only = Depends(require_role(UserRole.ADMIN))

@router.get("/dashboard", response_model=AdminDashboardResponse, summary="[Admin] Admin dashboard statistikasi")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    _ = admin_only
):
    return await ReportService.get_dashboard_summary(db)

@router.get("/users", response_model=list[UserResponse], summary="[Admin] Foydalanuvchilar ro'yxati")
async def admin_list_users(
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _ = admin_only
):
    return await UserService.get_all_users(db, search, role, is_active)

@router.get("/roles", response_model=list[RoleResponse], summary="[Admin] Rollar ro'yxati")
async def admin_list_roles(
    db: AsyncSession = Depends(get_db),
    _ = admin_only
):
    return await RBACService.get_all_roles(db)

@router.get("/permissions", response_model=list[PermissionResponse], summary="[Admin] Ruxsatlar ro'yxati")
async def admin_list_permissions(
    db: AsyncSession = Depends(get_db),
    _ = admin_only
):
    return await RBACService.get_all_permissions(db)
