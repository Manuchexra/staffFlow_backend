from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role, UserRole
from app.modules.rbac.schemas import (
    RoleCreate, RoleResponse, PermissionCreate, PermissionResponse, 
    AssignPermissions, AssignRoles
)
from app.modules.rbac.service import RBACService
from typing import List

router = APIRouter(prefix="/rbac", tags=["RBAC Management"])

# Faqat Admin rbac ni boshqara oladi
admin_only = Depends(require_role(UserRole.ADMIN))

@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(data: PermissionCreate, db: AsyncSession = Depends(get_db), _ = admin_only):
    return await RBACService.create_permission(db, data)

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(db: AsyncSession = Depends(get_db), _ = admin_only):
    return await RBACService.get_all_permissions(db)

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db), _ = admin_only):
    return await RBACService.create_role(db, data)

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(db: AsyncSession = Depends(get_db), _ = admin_only):
    return await RBACService.get_all_roles(db)

@router.post("/roles/{role_id}/permissions")
async def assign_permissions(role_id: int, data: AssignPermissions, db: AsyncSession = Depends(get_db), _ = admin_only):
    return await RBACService.assign_permissions_to_role(db, role_id, data.permission_ids)

@router.post("/users/{user_id}/roles")
async def assign_user_roles(user_id: int, data: AssignRoles, db: AsyncSession = Depends(get_db), _ = admin_only):
    return await RBACService.assign_roles_to_user(db, user_id, data.role_ids)
