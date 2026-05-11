from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, time
from app.modules.users.models import UserRole

class UserBase(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    full_name: str
    position: Optional[str] = None          # yangi
    avatar_url: Optional[str] = None 

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: str
    full_name: str
    password: str
    role: str = "employee"
    is_active: bool = True
    work_start_time: time = time(9,0)
    work_end_time: time = time(18,0)
    base_salary: float = 0.0
    expected_monthly_hours: float = 160.0
    avatar_url: Optional[str] = None      # yangi
    position: Optional[str] = None        # yangi

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    position: Optional[str] = None
    avatar_url: Optional[str] = None
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    base_salary: Optional[float] = None
    expected_monthly_hours: Optional[float] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    work_start_time: time
    work_end_time: time
    base_salary: float
    expected_monthly_hours: float
    created_at: datetime

    class Config:
        from_attributes = True
