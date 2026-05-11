from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role, UserRole, get_current_user
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdate, ChangePasswordRequest
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="[Admin] Yangi xodim yaratish")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN))
):
    return await UserService.create_user(db, user_data)

@router.get("/", response_model=list[UserResponse], summary="[Admin/HR] Barcha xodimlarni ko'rish")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await UserService.get_all_users(db)

@router.get("/me", response_model=UserResponse, summary="[Auth] O'z profilini ko'rish")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse, summary="[Auth] O'z profilini tahrirlash")
async def update_me(
    update_data: UserUpdate,
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

@router.post("/me/avatar", summary="[Auth] Avatar yuklash")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Foydalanuvchi o'z avatarini yuklaydi. Fayl serverda saqlanadi va qisqa URL qaytariladi.
    """
    try:
        avatar_url = await UserService.update_avatar(db, current_user.id, file)
        return {"avatar_url": avatar_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"ERROR Upload Avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Serverda xatolik yuz berdi: {str(e)}"
        )
