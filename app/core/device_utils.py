import hashlib
import uuid
from typing import Optional
from fastapi import Request

def generate_device_id(user_agent: str = None) -> str:
    """
    Qurilma ID yaratish. Agar qurilma ID yuborilmasa, 
    User-Agent va tasodifiy qiymatdan hash yaratish
    """
    if not user_agent:
        user_agent = str(uuid.uuid4())
    
    # Unique device ID yaratish
    device_string = f"{user_agent}_{uuid.uuid4()}"
    device_id = hashlib.sha256(device_string.encode()).hexdigest()[:32]
    return device_id

def extract_device_info(request: Request) -> dict:
    """
    Request'dan qurilma ma'lumotlarini chiqarish
    """
    user_agent = request.headers.get("user-agent", "")
    device_type = "mobile" if any(x in user_agent.lower() for x in ['android', 'iphone', 'mobile']) else "web"
    
    device_info = {
        "user_agent": user_agent,
        "device_type": device_type,
        "client_ip": request.client.host if request.client else None,
    }
    
    return device_info

def get_or_create_device_id(device_id: Optional[str] = None, user_agent: str = None) -> str:
    """
    Qurilma ID olish yoki yaratish
    
    Args:
        device_id: Yuborilgan device_id (agar mavjud bo'lsa)
        user_agent: User-Agent header
    
    Returns:
        Device ID string
    """
    if device_id:
        return device_id
    
    return generate_device_id(user_agent)
