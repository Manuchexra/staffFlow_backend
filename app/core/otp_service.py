import random
import json
from datetime import datetime, timedelta
from app.core.redis_client import redis_client
from app.core.email import send_otp_email

class OTPService:
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_OTP_ATTEMPTS = 3
    
    @staticmethod
    def generate_otp() -> str:
        """
        6 raqamli OTP kod yaratish
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(OTPService.OTP_LENGTH)])
    
    @staticmethod
    async def create_and_send_otp(user_id: int, email: str, user_name: str, device_id: str) -> dict:
        """
        OTP yaratish va emailga yuborish
        
        Args:
            user_id: User ID
            email: User emaili
            user_name: User nomi
            device_id: Qurilma ID
            
        Returns:
            dict: OTP yuborilgan ma'lumot
        """
        otp = OTPService.generate_otp()
        
        # OTP'ni Redis'da saqlash
        otp_key = f"otp:{user_id}:{device_id}"
        otp_data = {
            "otp": otp,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "email": email
        }
        
        # 10 daqiqa amal qilish vaqti bilan
        await redis_client.setex(
            otp_key,
            OTPService.OTP_EXPIRY_MINUTES * 60,
            json.dumps(otp_data)
        )
        
        # Emailga yuborish
        sent = await send_otp_email(email, otp, user_name)
        
        return {
            "success": sent,
            "message": "OTP emailiga yuborildi" if sent else "OTP yuborishda xatolik",
            "otp_id": otp_key,
            "expires_in_minutes": OTPService.OTP_EXPIRY_MINUTES
        }
    
    @staticmethod
    async def verify_otp(user_id: int, device_id: str, otp: str) -> dict:
        """
        OTP kodini tekshirish
        
        Args:
            user_id: User ID
            device_id: Qurilma ID
            otp: Kiritilgan OTP kod
            
        Returns:
            dict: Tekshirish natijasi
        """
        # TEST REJIM: 000000 har doim to'g'ri
        if otp == "000000":
            otp_key = f"otp:{user_id}:{device_id}"
            await redis_client.delete(otp_key)
            return {
                "success": True,
                "message": "OTP tasdiqlandi (Test rejim)"
            }
            
        otp_key = f"otp:{user_id}:{device_id}"
        otp_data_str = await redis_client.get(otp_key)
        
        if not otp_data_str:
            return {
                "success": False,
                "message": "OTP muddati tugadi. Qayta urinib ko'ring.",
                "is_expired": True
            }
        
        otp_data = json.loads(otp_data_str)
        
        # Urinishlar sonini tekshirish
        if otp_data["attempts"] >= OTPService.MAX_OTP_ATTEMPTS:
            await redis_client.delete(otp_key)
            return {
                "success": False,
                "message": "Juda ko'p urinishlar. OTP kodini qayta so'rang.",
                "is_max_attempts": True
            }
        
        # OTP kodini tekshirish
        if otp_data["otp"] == otp:
            await redis_client.delete(otp_key)
            return {
                "success": True,
                "message": "OTP tasdiqlandi"
            }
        
        # Noto'g'ri kod bo'lsa, urinishlar sonini oshirish
        otp_data["attempts"] += 1
        await redis_client.setex(
            otp_key,
            OTPService.OTP_EXPIRY_MINUTES * 60,
            json.dumps(otp_data)
        )
        
        remaining_attempts = OTPService.MAX_OTP_ATTEMPTS - otp_data["attempts"]
        return {
            "success": False,
            "message": f"Noto'g'ri kod. Qolgan urinishlar: {remaining_attempts}",
            "remaining_attempts": remaining_attempts
        }
    
    @staticmethod
    async def create_temp_auth_token(user_id: int, device_id: str) -> str:
        """
        Vaqtiy login tokeni yaratish (OTP tekshirish uchun)
        """
        temp_token_key = f"temp_auth:{user_id}:{device_id}"
        temp_token_data = {
            "user_id": user_id,
            "device_id": device_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 15 daqiqa amal qilish vaqti
        await redis_client.setex(
            temp_token_key,
            15 * 60,
            json.dumps(temp_token_data)
        )
        
        return temp_token_key
    
    @staticmethod
    async def verify_temp_auth_token(temp_token: str) -> dict:
        """
        Vaqtiy token tekshirish
        """
        token_data_str = await redis_client.get(temp_token)
        
        if not token_data_str:
            return {
                "success": False,
                "message": "Sessiya muddati tugadi"
            }
        
        return {
            "success": True,
            "data": json.loads(token_data_str)
        }
