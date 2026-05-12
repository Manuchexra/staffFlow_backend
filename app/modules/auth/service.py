from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.users.models import User
from app.core.security import verify_password, create_access_token, create_refresh_token, increment_failed_login, is_blocked, blacklist_token
from app.core.otp_service import OTPService
from fastapi import HTTPException, status
from app.core.redis_client import redis_client
import logging
from datetime import datetime, timedelta
import json
import asyncio
from app.core.email import send_otp_email

logger = logging.getLogger(__name__)

# Cache user lookups for 5 seconds to reduce DB queries
CACHE_TTL = 5

class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, identifier: str, password: str, device_id: str):
        """
        Authenticate user with phone or email and password.
        Optimized for performance with caching and minimal DB queries.
        """
        # Check if user is blocked due to failed attempts
        if await is_blocked(identifier):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to too many failed login attempts. Try again in 15 minutes.",
                headers={"Retry-After": "900"}
            )
        
        try:
            # Try to get user from cache first (optimized for performance)
            cache_key = f"user_cache:{identifier}"
            cached_user = await redis_client.get(cache_key)
            
            if cached_user:
                user_data = json.loads(cached_user)
                user_id = user_data["id"]
                hashed_password = user_data["hashed_password"]
                # Create a minimal user object for token generation
                user = type('User', (), {
                    'id': user_id,
                    'hashed_password': hashed_password,
                    'device_id': user_data.get("device_id"),
                    'email': user_data.get("email")
                })()
            else:
                # Query database only when cache miss
                stmt = select(User).where((User.phone == identifier) | (User.email == identifier))
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    await increment_failed_login(identifier)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials"
                    )
                
                # Cache user data for 5 seconds
                user_cache_data = {
                    "id": user.id,
                    "hashed_password": user.hashed_password,
                    "email": user.email,
                    "phone": user.phone
                }
                await redis_client.setex(cache_key, CACHE_TTL, json.dumps(user_cache_data))
            
            # Verify password (⚡ non-blocking via thread pool)
            if not await verify_password(password, user.hashed_password):
                await increment_failed_login(identifier)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Clear failed login attempts on successful authentication
            await redis_client.delete(f"login_fail:{identifier}")
            
            # Check device: if new device and we have an email, send OTP (fast)
            is_new_device = (getattr(user, 'device_id', None) is not None) and (user.device_id != device_id)
            if is_new_device and getattr(user, 'email', None):
                # Create temp auth token (short-lived) to complete OTP verification
                temp_token = await OTPService.create_temp_auth_token(user.id, device_id)

                # Generate OTP and store it immediately in Redis
                otp = OTPService.generate_otp()
                otp_key = f"otp:{user.id}:{device_id}"
                otp_data = {
                    "otp": otp,
                    "created_at": datetime.utcnow().isoformat(),
                    "attempts": 0,
                    "email": user.email
                }
                await redis_client.setex(otp_key, OTPService.OTP_EXPIRY_MINUTES * 60, json.dumps(otp_data))

                # Send email in background (don't await) to keep response fast
                try:
                    asyncio.create_task(send_otp_email(user.email, otp, getattr(user, 'first_name', 'Foydalanuvchi')))
                except Exception:
                    logger.warning("Failed to schedule OTP email send in background")

                return {
                    "requires_otp": True,
                    "temp_auth_token": temp_token,
                    "message": "OTP kodi emailiga yuborildi. Tasdiqlang.",
                    "expires_in_minutes": OTPService.OTP_EXPIRY_MINUTES
                }

            # For known devices (or direct login), generate tokens immediately
            # This branch supports response time < 2 seconds
            access_token = create_access_token(str(user.id))
            refresh_token = create_refresh_token(str(user.id))
            
            # Update device_id asynchronously (non-blocking) if real ORM object
            try:
                from app.modules.users.models import User as UserModel
                is_orm_user = isinstance(user, UserModel)
            except Exception:
                is_orm_user = False

            if is_orm_user:
                user.device_id = device_id
                db.add(user)
                # Don't await commit here to keep response time low
                try:
                    await db.commit()
                except Exception as e:
                    logger.warning(f"Device update failed: {e}")
            
            return {
                "requires_otp": False,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user.id,
                "device_id": device_id,
                "expires_in": 3600  # 1 hour in seconds
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service temporarily unavailable"
            )
    
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
        """Logout user by blacklisting token"""
        try:
            # Blacklist token for 1 hour (access token expiry)
            await blacklist_token(token, 3600)
            return {
                "message": "Successfully logged out",
                "detail": "Your access token has been invalidated"
            }
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )