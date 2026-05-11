from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.users.models import User
from app.core.security import verify_password, create_access_token, create_refresh_token, increment_failed_login, is_blocked, blacklist_token
from app.core.otp_service import OTPService
from fastapi import HTTPException, status
from app.core.redis_client import redis_client

class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, identifier: str, password: str, device_id: str):
        """Foydalanuvchini autentifikatsiya qilish"""
        if await is_blocked(identifier):
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Too many failed attempts. Try again in 15 minutes.")
        stmt = select(User).where((User.phone == identifier) | (User.email == identifier))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            await increment_failed_login(identifier)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        await redis_client.delete(f"login_fail:{identifier}")
        
        # Yangi qurilma yoki eski qurilmani tekshirish
        is_new_device = user.device_id != device_id
        
        if is_new_device and user.email:
            # Yangi qurilma - OTP yuborish kerak
            await OTPService.create_and_send_otp(
                user_id=user.id,
                email=user.email,
                user_name=user.first_name,
                device_id=device_id
            )
            
            # Vaqtiy token yaratish
            temp_token = await OTPService.create_temp_auth_token(user.id, device_id)
            
            return {
                "requires_otp": True,
                "temp_auth_token": temp_token,
                "message": "OTP kodi emailiga yuborildi. Tasdiqlang.",
                "expires_in_minutes": OTPService.OTP_EXPIRY_MINUTES
            }
        else:
            # Ma'lum qurilma - to'g'ridan-to'g'ri login
            user.device_id = device_id
            db.add(user)
            await db.commit()
            
            access = create_access_token(str(user.id))
            refresh = create_refresh_token(str(user.id))
            
            return {
                "requires_otp": False,
                "access_token": access,
                "refresh_token": refresh,
                "user_id": user.id,
                "device_id": user.device_id
            }
    
    @staticmethod
    async def verify_otp_and_complete_login(db: AsyncSession, temp_auth_token: str, otp: str):
        """OTP ni tekshirish va logini yakunlash"""
        # Vaqtiy tokenni tekshirish
        temp_auth_result = await OTPService.verify_temp_auth_token(temp_auth_token)
        if not temp_auth_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessiya muddati tugadi. Qayta login qiling."
            )
        
        temp_auth_data = temp_auth_result["data"]
        user_id = temp_auth_data["user_id"]
        device_id = temp_auth_data["device_id"]
        
        # OTP ni tekshirish
        otp_verify_result = await OTPService.verify_otp(user_id, device_id, otp)
        if not otp_verify_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=otp_verify_result["message"]
            )
        
        # User'ni olish va device_id ni saqlash
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.device_id = device_id
        db.add(user)
        await db.commit()
        
        # Token yaratish
        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        
        return {
            "access_token": access,
            "refresh_token": refresh,
            "user_id": user.id,
            "device_id": user.device_id
        }

    @staticmethod
    async def logout(token: str):
        # Access tokenni 60 daqiqaga blacklistga qo'shish
        await blacklist_token(token, 3600)
        return {"detail": "Successfully logged out"}