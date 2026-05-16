from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.modules.rbac.models import Role, Permission, user_roles, role_permissions
from app.modules.rbac.schemas import RoleCreate, PermissionCreate, RoleUpdate
from fastapi import HTTPException, status
from app.modules.users.models import User

class RBACService:
    # --- Permission Operations ---
    @staticmethod
    async def create_permission(db: AsyncSession, data: PermissionCreate):
        stmt = select(Permission).where(Permission.name == data.name)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Permission already exists")
        
        permission = Permission(**data.model_dump())
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        return permission

    @staticmethod
    async def get_all_permissions(db: AsyncSession):
        res = await db.execute(select(Permission))
        return res.scalars().all()

    # --- Role Operations ---
    @staticmethod
    async def create_role(db: AsyncSession, data: RoleCreate):
        stmt = select(Role).where(Role.name == data.name)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Role already exists")
        
        role = Role(**data.model_dump())
        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def get_all_roles(db: AsyncSession):
        res = await db.execute(select(Role).options(selectinload(Role.permissions)))
        return res.scalars().all()

    @staticmethod
    async def assign_permissions_to_role(db: AsyncSession, role_id: int, permission_ids: list[int]):
        # selectinload orqali permissionlarni ham yuklaymiz, shunda o'zgartirishda lazy loading xatosi bo'lmaydi
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
        res = await db.execute(stmt)
        role = res.scalar_one_or_none()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        stmt_p = select(Permission).where(Permission.id.in_(permission_ids))
        permissions = (await db.execute(stmt_p)).scalars().all()
        
        role.permissions = list(permissions)
        await db.commit()
        # Refresh qilganda ham relationshipni saqlab qolish uchun options ishlatamiz
        stmt_final = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
        res_final = await db.execute(stmt_final)
        return res_final.scalar_one()

    # --- User-Role Assignments ---
    @staticmethod
    async def assign_roles_to_user(db: AsyncSession, user_id: int, role_ids: list[int]):
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Eski rollarni o'chirish (Agar required bo'lsa)
        await db.execute(delete(user_roles).where(user_roles.c.user_id == user_id))
        
        # Yangi rollarni qo'shish
        for r_id in role_ids:
            await db.execute(user_roles.insert().values(user_id=user_id, role_id=r_id))
        
        await db.commit()
        return {"message": "Roles assigned successfully"}

    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: int) -> set[str]:
        """Userning barcha rollaridan permissionlarni yig'ib olish"""
        stmt = select(Permission.name).join(role_permissions).join(Role).join(user_roles).where(user_roles.c.user_id == user_id)
        res = await db.execute(stmt)
        return set(res.scalars().all())
