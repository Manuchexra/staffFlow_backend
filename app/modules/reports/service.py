from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, extract
from app.modules.users.models import User
from app.modules.attendance.models import Attendance
from app.modules.salary.models import Salary
from datetime import date, datetime
from app.modules.reports.schemas import AttendanceReportItem, SalaryReportItem

class ReportService:
    # 1. Dashboard Summary
    @staticmethod
    async def get_dashboard_summary(db: AsyncSession):
        total_employees = (await db.execute(select(func.count(User.id)))).scalar()
        active_employees = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
        
        today = date.today()
        present_today = (await db.execute(select(func.count(func.distinct(Attendance.user_id))).where(func.date(Attendance.check_in_time) == today))).scalar()
        late_today = (await db.execute(select(func.count(func.distinct(Attendance.user_id))).where(and_(func.date(Attendance.check_in_time) == today, Attendance.late_minutes > 0)))).scalar()
        
        now = datetime.now()
        total_payroll = (await db.execute(select(func.sum(Salary.net_salary)).where(and_(Salary.month == now.month, Salary.year == now.year)))).scalar() or 0
        
        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "present_today": present_today,
            "late_today": late_today,
            "total_payroll_month": float(total_payroll)
        }

    # 2. Daily Attendance
    @staticmethod
    async def get_daily_attendance(db: AsyncSession, target_date: date):
        stmt = select(Attendance, User).join(User, Attendance.user_id == User.id).where(func.date(Attendance.check_in_time) == target_date)
        res = await db.execute(stmt)
        data = res.all()
        return [{"user_id": u.id, "full_name": f"{u.first_name} {u.last_name}", "check_in": a.check_in_time, "late": a.late_minutes} for a, u in data]

    # 3. Monthly Attendance Summary
    @staticmethod
    async def get_monthly_attendance(db: AsyncSession, month: int, year: int):
        stmt = select(
            User.id, User.first_name, User.last_name,
            func.count(Attendance.id).label("days"),
            func.sum(Attendance.worked_hours).label("hours"),
            func.sum(Attendance.late_minutes).label("total_late")
        ).outerjoin(Attendance, and_(
            User.id == Attendance.user_id,
            extract('month', Attendance.check_in_time) == month,
            extract('year', Attendance.check_in_time) == year
        )).group_by(User.id)
        
        res = await db.execute(stmt)
        rows = res.all()
        return [{"user_id": r.id, "full_name": f"{r.first_name} {r.last_name}", "days_present": r.days, "total_hours": float(r.hours or 0), "total_late_min": int(r.total_late or 0)} for r in rows]

    # 4. Attendance Report (Detailed per period)
    @staticmethod
    async def get_attendance_report(db: AsyncSession, start_date: date, end_date: date):
        stmt = select(
            User.id, User.first_name, User.last_name,
            func.count(Attendance.id).label("total_entries"),
            func.sum(Attendance.worked_hours).label("total_hours"),
            func.sum(Attendance.late_minutes).label("late_mins")
        ).outerjoin(Attendance, and_(
            User.id == Attendance.user_id,
            func.date(Attendance.check_in_time) >= start_date,
            func.date(Attendance.check_in_time) <= end_date
        )).group_by(User.id)

        result = await db.execute(stmt)
        rows = result.all()
        days_in_period = (end_date - start_date).days + 1
        
        report = []
        for row in rows:
            report.append(AttendanceReportItem(
                user_id=row.id,
                full_name=f"{row.first_name} {row.last_name}",
                total_days=days_in_period,
                present_days=row.total_entries or 0,
                absent_days=max(0, days_in_period - (row.total_entries or 0)),
                late_days=1 if (row.late_mins or 0) > 0 else 0, # Soddalashtirilgan
                total_hours=float(row.total_hours or 0)
            ))
        return report

    # 5. Salary Summary
    @staticmethod
    async def get_salary_summary(db: AsyncSession, month: int, year: int):
        stmt = select(
            func.sum(Salary.net_salary).label("total"),
            func.avg(Salary.net_salary).label("avg"),
            func.max(Salary.net_salary).label("max"),
            func.min(Salary.net_salary).label("min")
        ).where(and_(Salary.month == month, Salary.year == year))
        res = await db.execute(stmt)
        row = res.first()
        return {
            "total_fund": float(row.total or 0),
            "average_salary": float(row.avg or 0),
            "max_salary": float(row.max or 0),
            "min_salary": float(row.min or 0)
        }

    # 6. Detailed Salary Report
    @staticmethod
    async def get_salary_report(db: AsyncSession, month: int, year: int):
        stmt = select(Salary, User).join(User, Salary.user_id == User.id).where(
            and_(Salary.month == month, Salary.year == year)
        )
        result = await db.execute(stmt)
        data = result.all()
        
        report = []
        for sal, user in data:
            report.append(SalaryReportItem(
                user_id=user.id,
                full_name=f"{user.first_name} {user.last_name}",
                base_salary=sal.base_salary,
                bonuses=sal.bonus_total,
                penalties=sal.penalty_total,
                advances=sal.advance_total,
                net_salary=sal.net_salary,
                status=sal.status.value
            ))
        return report

    # 9. Top Performers
    @staticmethod
    async def get_top_performers(db: AsyncSession, limit: int = 5):
        stmt = select(User, func.sum(Attendance.worked_hours).label("total_hours"))\
            .join(Attendance).group_by(User.id).order_by(desc("total_hours")).limit(limit)
        res = await db.execute(stmt)
        data = res.all()
        return [{"user_id": u.id, "full_name": f"{u.first_name} {u.last_name}", "total_hours": float(h)} for u, h in data]
