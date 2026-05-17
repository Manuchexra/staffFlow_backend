from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, extract, or_
from datetime import date, datetime, time
from typing import Dict, Any

from app.modules.users.models import User, UserRole
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.salary.models import Salary, SalaryStatus, Transaction, TransactionType
from app.modules.shifts.models import Shift, EmployeeShift
from app.modules.notifications.models import Notification

class DashboardService:
    @staticmethod
    async def get_admin_dashboard(db: AsyncSession) -> Dict[str, Any]:
        # 1. Total users
        total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
        
        # 2. Role distribution
        admins_count = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.ADMIN))).scalar() or 0
        hr_managers_count = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.HR_MANAGER))).scalar() or 0
        employees_count = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.EMPLOYEE))).scalar() or 0
        
        # 3. Status distribution
        active_count = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
        inactive_count = (await db.execute(select(func.count(User.id)).where(User.is_active == False))).scalar() or 0
        
        # 4. Today's attendance
        today = date.today()
        present_today = (await db.execute(
            select(func.count(func.distinct(Attendance.user_id)))
            .where(func.date(Attendance.check_in_time) == today)
        )).scalar() or 0
        
        late_today = (await db.execute(
            select(func.count(func.distinct(Attendance.user_id)))
            .where(and_(func.date(Attendance.check_in_time) == today, Attendance.late_minutes > 0))
        )).scalar() or 0
        
        # Absents: Active employees (staff) who have not checked in today
        active_employees = (await db.execute(
            select(func.count(User.id)).where(and_(User.is_active == True, User.role == UserRole.EMPLOYEE))
        )).scalar() or 0
        absent_today = max(0, active_employees - present_today)
        
        # 5. Salary overview for current month
        now = datetime.now()
        total_payroll_calculated = (await db.execute(
            select(func.sum(Salary.net_salary))
            .where(and_(Salary.month == now.month, Salary.year == now.year))
        )).scalar() or 0.0
        
        total_payroll_paid = (await db.execute(
            select(func.sum(Salary.net_salary))
            .where(and_(Salary.month == now.month, Salary.year == now.year, Salary.status == SalaryStatus.PAID))
        )).scalar() or 0.0
        
        average_salary = (await db.execute(
            select(func.avg(User.base_salary)).where(User.role == UserRole.EMPLOYEE)
        )).scalar() or 0.0
        
        # 6. Total active shifts
        total_active_shifts = (await db.execute(select(func.count(Shift.id)))).scalar() or 0
        
        # 7. Total notifications sent
        total_notifications_sent = (await db.execute(select(func.count(Notification.id)))).scalar() or 0
        
        return {
            "total_users": total_users,
            "roles": {
                "admins_count": admins_count,
                "hr_managers_count": hr_managers_count,
                "employees_count": employees_count
            },
            "status": {
                "active_count": active_count,
                "inactive_count": inactive_count
            },
            "attendance_today": {
                "present_today": present_today,
                "late_today": late_today,
                "absent_today": absent_today
            },
            "salary_overview": {
                "total_payroll_calculated": float(total_payroll_calculated),
                "total_payroll_paid": float(total_payroll_paid),
                "average_salary": float(average_salary)
            },
            "total_active_shifts": total_active_shifts,
            "total_notifications_sent": total_notifications_sent
        }

    @staticmethod
    async def get_hr_dashboard(db: AsyncSession) -> Dict[str, Any]:
        # 1. Today's attendance
        today = date.today()
        present_today = (await db.execute(
            select(func.count(func.distinct(Attendance.user_id)))
            .where(func.date(Attendance.check_in_time) == today)
        )).scalar() or 0
        
        late_today = (await db.execute(
            select(func.count(func.distinct(Attendance.user_id)))
            .where(and_(func.date(Attendance.check_in_time) == today, Attendance.late_minutes > 0))
        )).scalar() or 0
        
        on_time_today = max(0, present_today - late_today)
        
        active_employees_cnt = (await db.execute(
            select(func.count(User.id)).where(and_(User.is_active == True, User.role == UserRole.EMPLOYEE))
        )).scalar() or 0
        absent_today = max(0, active_employees_cnt - present_today)
        
        # Average check in time today
        check_ins_res = await db.execute(
            select(Attendance.check_in_time).where(func.date(Attendance.check_in_time) == today)
        )
        check_in_times = check_ins_res.scalars().all()
        avg_check_in_str = None
        if check_in_times:
            total_minutes = sum(t.hour * 60 + t.minute for t in check_in_times)
            avg_minutes = total_minutes // len(check_in_times)
            avg_hour = avg_minutes // 60
            avg_min = avg_minutes % 60
            avg_check_in_str = f"{avg_hour:02d}:{avg_min:02d}"

        # 2. Monthly Stats (Current Month)
        now = datetime.now()
        # Top 5 late employees this month
        top_late_res = await db.execute(
            select(User, func.sum(Attendance.late_minutes).label("total_late"))
            .join(Attendance, User.id == Attendance.user_id)
            .where(and_(
                extract('month', Attendance.check_in_time) == now.month,
                extract('year', Attendance.check_in_time) == now.year,
                Attendance.late_minutes > 0
            ))
            .group_by(User.id)
            .order_by(desc("total_late"))
            .limit(5)
        )
        top_late_data = top_late_res.all()
        top_late_employees = [
            {
                "user_id": u.id,
                "full_name": f"{u.first_name} {u.last_name}",
                "value": float(total_late),
                "position": u.position
            }
            for u, total_late in top_late_data
        ]

        # Top 5 performers this month (based on worked hours)
        top_performers_res = await db.execute(
            select(User, func.sum(Attendance.worked_hours).label("total_hours"))
            .join(Attendance, User.id == Attendance.user_id)
            .where(and_(
                extract('month', Attendance.check_in_time) == now.month,
                extract('year', Attendance.check_in_time) == now.year
            ))
            .group_by(User.id)
            .order_by(desc("total_hours"))
            .limit(5)
        )
        top_performers_data = top_performers_res.all()
        top_performers = [
            {
                "user_id": u.id,
                "full_name": f"{u.first_name} {u.last_name}",
                "value": float(total_hours),
                "position": u.position
            }
            for u, total_hours in top_performers_data
        ]

        # 3. Salary overview (Current Month)
        total_calculated = (await db.execute(
            select(func.sum(Salary.net_salary))
            .where(and_(Salary.month == now.month, Salary.year == now.year))
        )).scalar() or 0.0
        
        total_unpaid_calculations = (await db.execute(
            select(func.count(Salary.id))
            .where(and_(Salary.month == now.month, Salary.year == now.year, Salary.status == SalaryStatus.CALCULATED))
        )).scalar() or 0
        
        total_bonuses = (await db.execute(
            select(func.sum(Transaction.amount))
            .where(and_(
                Transaction.type == TransactionType.BONUS,
                extract('month', Transaction.date) == now.month,
                extract('year', Transaction.date) == now.year
            ))
        )).scalar() or 0.0
        
        total_penalties = (await db.execute(
            select(func.sum(Transaction.amount))
            .where(and_(
                Transaction.type == TransactionType.PENALTY,
                extract('month', Transaction.date) == now.month,
                extract('year', Transaction.date) == now.year
            ))
        )).scalar() or 0.0

        # 4. Employees without shifts today
        # Select active employees who don't have a record in employee_shifts for today
        subq = select(EmployeeShift.user_id).where(EmployeeShift.date == today)
        no_shift_res = await db.execute(
            select(User)
            .where(and_(
                User.is_active == True,
                User.role == UserRole.EMPLOYEE,
                ~User.id.in_(subq)
            ))
        )
        no_shift_users = no_shift_res.scalars().all()
        employees_without_shifts = [
            {
                "user_id": u.id,
                "full_name": f"{u.first_name} {u.last_name}",
                "phone": u.phone,
                "position": u.position
            }
            for u in no_shift_users
        ]

        return {
            "attendance_today": {
                "present_today": present_today,
                "late_today": late_today,
                "on_time_today": on_time_today,
                "absent_today": absent_today,
                "avg_check_in_time": avg_check_in_str
            },
            "top_late_employees_month": top_late_employees,
            "top_performers_month": top_performers,
            "salary_overview": {
                "total_calculated": float(total_calculated),
                "total_unpaid_calculations": total_unpaid_calculations,
                "total_bonuses": float(total_bonuses),
                "total_penalties": float(total_penalties)
            },
            "employees_without_shifts_today": employees_without_shifts
        }

    @staticmethod
    async def get_employee_dashboard(db: AsyncSession, current_user: User) -> Dict[str, Any]:
        # 1. Profile Summary
        profile = {
            "id": current_user.id,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role.value,
            "position": current_user.position,
            "work_type": current_user.work_type.value,
            "work_start_time": current_user.work_start_time.strftime("%H:%M:%S") if current_user.work_start_time else "09:00:00",
            "work_end_time": current_user.work_end_time.strftime("%H:%M:%S") if current_user.work_end_time else "18:00:00",
            "avatar_url": current_user.avatar_url
        }

        # 2. Today's Attendance status
        today = date.today()
        att_res = await db.execute(
            select(Attendance).where(and_(
                Attendance.user_id == current_user.id,
                func.date(Attendance.check_in_time) == today
            ))
        )
        attendance = att_res.scalar_one_or_none()
        
        attendance_today = {
            "checked_in": attendance is not None,
            "check_in_time": attendance.check_in_time if attendance else None,
            "checked_out": (attendance is not None and attendance.status == AttendanceStatus.CHECKED_OUT),
            "check_out_time": attendance.check_out_time if (attendance and attendance.status == AttendanceStatus.CHECKED_OUT) else None,
            "worked_hours": float(attendance.worked_hours) if attendance else 0.0,
            "late_minutes": attendance.late_minutes if attendance else 0,
            "status": attendance.status.value if attendance else None
        }

        # 3. Monthly stats (Current Month)
        now = datetime.now()
        days_present = (await db.execute(
            select(func.count(Attendance.id)).where(and_(
                Attendance.user_id == current_user.id,
                extract('month', Attendance.check_in_time) == now.month,
                extract('year', Attendance.check_in_time) == now.year
            ))
        )).scalar() or 0
        
        total_worked_hours = (await db.execute(
            select(func.sum(Attendance.worked_hours)).where(and_(
                Attendance.user_id == current_user.id,
                extract('month', Attendance.check_in_time) == now.month,
                extract('year', Attendance.check_in_time) == now.year
            ))
        )).scalar() or 0.0
        
        total_late_minutes = (await db.execute(
            select(func.sum(Attendance.late_minutes)).where(and_(
                Attendance.user_id == current_user.id,
                extract('month', Attendance.check_in_time) == now.month,
                extract('year', Attendance.check_in_time) == now.year
            ))
        )).scalar() or 0
        
        monthly_stats = {
            "days_present": days_present,
            "total_worked_hours": float(total_worked_hours),
            "total_late_minutes": int(total_late_minutes)
        }

        # 4. Next/Today shift details
        shift_res = await db.execute(
            select(EmployeeShift, Shift)
            .join(Shift, EmployeeShift.shift_id == Shift.id)
            .where(and_(
                EmployeeShift.user_id == current_user.id,
                EmployeeShift.date == today
            ))
        )
        shift_data = shift_res.first()
        today_shift = None
        if shift_data:
            emp_shift, shift = shift_data
            today_shift = {
                "shift_id": shift.id,
                "name": shift.name,
                "start_time": shift.start_time.strftime("%H:%M:%S"),
                "end_time": shift.end_time.strftime("%H:%M:%S"),
                "date": emp_shift.date
            }

        # 5. Financial Summary (Current Month / Last calculated salary)
        bonuses = (await db.execute(
            select(func.sum(Transaction.amount)).where(and_(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.BONUS,
                extract('month', Transaction.date) == now.month,
                extract('year', Transaction.date) == now.year
            ))
        )).scalar() or 0.0
        
        penalties = (await db.execute(
            select(func.sum(Transaction.amount)).where(and_(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.PENALTY,
                extract('month', Transaction.date) == now.month,
                extract('year', Transaction.date) == now.year
            ))
        )).scalar() or 0.0
        
        advances = (await db.execute(
            select(func.sum(Transaction.amount)).where(and_(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.ADVANCE,
                extract('month', Transaction.date) == now.month,
                extract('year', Transaction.date) == now.year
            ))
        )).scalar() or 0.0
        
        # Last calculated salary
        last_sal_res = await db.execute(
            select(Salary)
            .where(Salary.user_id == current_user.id)
            .order_by(desc(Salary.year), desc(Salary.month))
            .limit(1)
        )
        last_sal = last_sal_res.scalar_one_or_none()
        last_salary_details = None
        if last_sal:
            last_salary_details = {
                "month": last_sal.month,
                "year": last_sal.year,
                "net_salary": float(last_sal.net_salary),
                "status": last_sal.status.value
            }
            
        financial_summary = {
            "base_salary": float(current_user.base_salary),
            "current_month_bonuses": float(bonuses),
            "current_month_penalties": float(penalties),
            "current_month_advances": float(advances),
            "last_salary": last_salary_details
        }

        # 6. Notifications
        unread_cnt = (await db.execute(
            select(func.count(Notification.id)).where(and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            ))
        )).scalar() or 0
        
        recent_notifs_res = await db.execute(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(desc(Notification.created_at))
            .limit(5)
        )
        recent_notifs = recent_notifs_res.scalars().all()
        recent_notifications = [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type.value,
                "is_read": n.is_read,
                "created_at": n.created_at
            }
            for n in recent_notifs
        ]

        return {
            "profile": profile,
            "attendance_today": attendance_today,
            "monthly_stats": monthly_stats,
            "today_shift": today_shift,
            "financial_summary": financial_summary,
            "unread_notifications_count": unread_cnt,
            "recent_notifications": recent_notifications
        }
