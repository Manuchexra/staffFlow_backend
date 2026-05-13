from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role, UserRole, get_current_user
from app.modules.users.models import User
from typing import Optional, Union
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdateMe, UserUpdateHR, ChangePasswordRequest, AdminResetPasswordRequest
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="[Admin/HR] Yangi xodim yaratish")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await UserService.create_user(db, user_data)

@router.get("/", response_model=list[UserResponse], summary="[Admin/HR] Barcha xodimlarni ko'rish va qidirish")
async def list_users(
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Xodimlarni ism, telefon yoki email bo'yicha qidirish, rol va holat bo'yicha filtrlash.
    """
    return await UserService.get_all_users(db, search, role, is_active)

@router.get("/{user_id}", response_model=UserResponse, summary="[Admin/HR] Xodim ma'lumotlarini ko'rish")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await UserService.get_user_by_id(db, user_id)

@router.patch("/{user_id}", response_model=UserResponse, summary="[Admin/HR] Xodim ma'lumotlarini tahrirlash")
async def update_user(
    user_id: int,
    update_data: UserUpdateHR,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Xodimning roli, maoshi, holati va boshqa ma'lumotlarini yangilash.
    """
    return await UserService.update_user(db, user_id, update_data)

@router.get("/me", response_model=UserResponse, summary="[Auth] O'z profilini ko'rish")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse, summary="[Auth] O'z profilini tahrirlash")
async def update_me(
    update_data: UserUpdateMe,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await UserService.update_user(db, current_user.id, update_data)

@router.post("/me/change-password", summary="[Auth] Parolni o'zgartirish")
async def change_my_password(
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await UserService.change_password(db, current_user.id, req.old_password, req.new_password)
    return {"message": "Password changed successfully"}

@router.post("/me/avatar", summary="[Auth] O'z avatarini yuklash")
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await UserService.update_avatar(db, current_user.id, file)

@router.post("/{user_id}/avatar", summary="[Admin/HR] Xodim uchun avatar yuklash")
async def upload_user_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    HR menejeri xodim uchun rasm yuklaydi.
    """
    avatar_url = await UserService.update_avatar(db, user_id, file)
    return {"avatar_url": avatar_url}

@router.post("/{user_id}/reset-password", summary="[Admin/HR] Xodim parolini yangilash")
async def admin_reset_user_password(
    user_id: int,
    req: AdminResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Xodim parolini HR menejeri tomonidan majburiy o'zgartirish.
    """
    await UserService.admin_set_password(db, user_id, req.new_password)
    return {"message": "Xodim paroli muvaffaqiyatli yangilandi"}

@router.delete("/{user_id}", summary="[Admin/HR] Xodimni o'chirish")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Xodim profilini tizimdan butunlay o'chirish.
    """
    await UserService.delete_user(db, user_id)
    return {"message": "Xodim muvaffaqiyatli o'chirildi"}
