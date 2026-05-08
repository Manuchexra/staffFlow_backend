from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role, UserRole
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN))
):
    """
    Faqat Admin yangi xodimlarni yarata oladi.
    """
    return await UserService.create_user(db, user_data)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.ADMIN))
):
    """
    Faqat Admin barcha xodimlarni ko'ra oladi.
    """
    return await UserService.get_all_users(db)
