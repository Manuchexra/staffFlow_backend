from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.modules.notifications.models import NotificationType
from app.modules.users.models import UserRole

class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO

class NotificationCreate(NotificationBase):
    user_id: Optional[int] = None # Agar bitta userga bo'lsa
    role: Optional[UserRole] = None # Agar ma'lum roldagilarga bo'lsa
    to_all: bool = False # Agar hammaga bo'lsa

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceTokenCreate(BaseModel):
    fcm_token: str
    device_type: Optional[str] = "web"
