from pydantic import BaseModel
from typing import Optional

class AdminDashboardResponse(BaseModel):
    total_employees: int
    active_employees: int
    present_today: int
    late_today: int
    total_payroll_month: float
    hr_employees: Optional[int] = None
    admin_users: Optional[int] = None

    class Config:
        from_attributes = True
