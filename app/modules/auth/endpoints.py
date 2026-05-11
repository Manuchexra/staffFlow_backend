from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.auth.schemas import LoginRequest, TokenResponse, VerifyOTPRequest, OTPResponse
from app.modules.auth.service import AuthService
from app.core.deps import security, get_current_user
from app.core.device_utils import get_or_create_device_id

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login(login_data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Tizimga kirish - 1-qadam: Username va parol
    Yangi qurilmadan kirilsa, OTP yuborishi kerak
    """
    # Device ID avtomatik yaratish (qurilma ma'lumotlari asosida)
    user_agent = request.headers.get("user-agent", "")
    device_id = get_or_create_device_id(None, user_agent)
    
    result = await AuthService.authenticate(db, login_data.identifier, login_data.password, device_id)
    
    if result.get("requires_otp"):
        # Yangi qurilma - OTP tasdiqlanishi kerak
        return OTPResponse(
            temp_auth_token=result["temp_auth_token"],
            message=result["message"],
            expires_in_minutes=result["expires_in_minutes"]
        )
    else:
        # Ma'lum qurilma - to'g'ridan-to'g'ri token qaytarish
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user_id=result["user_id"],
            device_id=result["device_id"]
        )

@router.post("/verify-otp", response_model=TokenResponse, summary="[Auth] OTP tasdiqlaması")
async def verify_otp(otp_request: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    OTP kodini tasdiqlaması va logini yakunlash
    Yangi qurilmadan login qilgandan keyin OTP'ni tekshirish uchun
    """
    result = await AuthService.verify_otp_and_complete_login(
        db, 
        otp_request.temp_auth_token, 
        otp_request.otp
    )
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user_id=result["user_id"],
        device_id=result["device_id"]
    )

@router.post("/logout", summary="[Auth] Tizimdan chiqish")
async def logout(
    credentials = Depends(security),
    current_user = Depends(get_current_user)
):
    token = credentials.credentials
    return await AuthService.logout(token)