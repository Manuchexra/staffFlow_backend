from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class DashboardSummary(BaseModel):
    total_employees: int
    active_employees: int
    present_today: int
    late_today: int
    total_payroll_month: float # Joriy oydagi umumiy hisoblangan maoshlar

class AttendanceReportItem(BaseModel):
    user_id: int
    full_name: str
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    total_hours: float

class SalaryReportItem(BaseModel):
    user_id: int
    full_name: str
    base_salary: float
    bonuses: float
    penalties: float
    advances: float
    net_salary: float
    status: str

class ReportFilter(BaseModel):
    start_date: date
    end_date: date
    department: Optional[str] = None # Kelajak uchun
