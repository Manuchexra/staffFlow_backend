from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.core.deps import security, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse, summary="[Public] Tizimga kirish")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    access, refresh = await AuthService.authenticate(db, login_data.identifier, login_data.password)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/logout", summary="[Auth] Tizimdan chiqish")
async def logout(
    credentials = Depends(security),
    current_user = Depends(get_current_user)
):
    token = credentials.credentials
    return await AuthService.logout(token)