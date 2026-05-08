from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, time
from app.modules.users.models import UserRole

class UserBase(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    full_name: str

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True
    work_start_time: time = time(9, 0)
    work_end_time: time = time(18, 0)
    base_salary: float = 0.0
    expected_monthly_hours: float = 160.0

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
