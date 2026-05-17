from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, time, datetime

# --- ADMIN DASHBOARD ---
class AdminRoleDistribution(BaseModel):
    admins_count: int
    hr_managers_count: int
    employees_count: int

class AdminStatusDistribution(BaseModel):
    active_count: int
    inactive_count: int

class AdminAttendanceToday(BaseModel):
    present_today: int
    late_today: int
    absent_today: int

class AdminSalaryOverview(BaseModel):
    total_payroll_calculated: float
    total_payroll_paid: float
    average_salary: float

class AdminDashboardResponse(BaseModel):
    total_users: int
    roles: AdminRoleDistribution
    status: AdminStatusDistribution
    attendance_today: AdminAttendanceToday
    salary_overview: AdminSalaryOverview
    total_active_shifts: int
    total_notifications_sent: int


# --- HR DASHBOARD ---
class HRAttendanceToday(BaseModel):
    present_today: int
    late_today: int
    on_time_today: int
    absent_today: int
    avg_check_in_time: Optional[str] = None  # masalan "09:15"

class HREmployeeStatItem(BaseModel):
    user_id: int
    full_name: str
    value: float  # kechikkan daqiqalari yoki ish soatlari
    position: Optional[str] = None

class HRSalaryOverview(BaseModel):
    total_calculated: float
    total_unpaid_calculations: int
    total_bonuses: float
    total_penalties: float

class HREmployeeWithoutShift(BaseModel):
    user_id: int
    full_name: str
    phone: str
    position: Optional[str] = None

class HRDashboardResponse(BaseModel):
    attendance_today: HRAttendanceToday
    top_late_employees_month: List[HREmployeeStatItem]
    top_performers_month: List[HREmployeeStatItem]
    salary_overview: HRSalaryOverview
    employees_without_shifts_today: List[HREmployeeWithoutShift]


# --- EMPLOYEE DASHBOARD ---
class EmployeeProfileSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    role: str
    position: Optional[str] = None
    work_type: str
    work_start_time: str
    work_end_time: str
    avatar_url: Optional[str] = None

class EmployeeAttendanceToday(BaseModel):
    checked_in: bool
    check_in_time: Optional[datetime] = None
    checked_out: bool
    check_out_time: Optional[datetime] = None
    worked_hours: float
    late_minutes: int
    status: Optional[str] = None

class EmployeeMonthlyStats(BaseModel):
    days_present: int
    total_worked_hours: float
    total_late_minutes: int

class EmployeeShiftDetail(BaseModel):
    shift_id: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    date: Optional[date] = None

class EmployeeFinancialSummary(BaseModel):
    base_salary: float
    current_month_bonuses: float
    current_month_penalties: float
    current_month_advances: float
    last_salary: Optional[Dict[str, Any]] = None  # {"month": 5, "year": 2026, "net_salary": 5000000.0, "status": "paid"}

class EmployeeNotificationItem(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

class EmployeeDashboardResponse(BaseModel):
    profile: EmployeeProfileSummary
    attendance_today: EmployeeAttendanceToday
    monthly_stats: EmployeeMonthlyStats
    today_shift: Optional[EmployeeShiftDetail] = None
    financial_summary: EmployeeFinancialSummary
    unread_notifications_count: int
    recent_notifications: List[EmployeeNotificationItem]
