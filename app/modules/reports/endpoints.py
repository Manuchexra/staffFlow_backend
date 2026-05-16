from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.core.deps import require_role, UserRole
from app.modules.reports.service import ReportService
from app.modules.users.models import User
from app.modules.salary.models import Salary
from app.modules.attendance.models import Attendance
from typing import List, Optional
from datetime import date, datetime

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

# 1. Dashboard Summary
@router.get("/dashboard/summary", summary="[Admin/HR] Asosiy dashboard ko‘rsatkichlari")
async def get_summary(db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    return await ReportService.get_dashboard_summary(db)

# 2. Daily Attendance
@router.get("/attendance/daily", summary="[Admin/HR] Kunlik davomat statistikasi", description="Sana formati: YYYY-MM-DD (Masalan: 2026-05-16)")
async def get_daily_attendance(target_date: date = Query(default=date.today(), description="Sana formati: YYYY-MM-DD"), db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    return await ReportService.get_daily_attendance(db, target_date)

# 3. Monthly Attendance Summary
@router.get("/attendance/monthly", summary="[Admin/HR] Oylik davomat jamlanmasi")
async def get_monthly_attendance(month: int = Query(...), year: int = Query(...), db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    return await ReportService.get_monthly_attendance(db, month, year)

# 4. Employee Attendance Report
@router.get("/attendance/employee/{user_id}", summary="[Admin/HR] Muayyan xodimning davomat hisoboti", description="Sana formati: YYYY-MM-DD (Masalan: 2026-05-01). Path parametrdagi xodim ID si bo'yicha filtrlanadi.")
async def get_employee_attendance(
    user_id: int, 
    start_date: date = Query(..., description="Boshlanish sanasi: YYYY-MM-DD"), 
    end_date: date = Query(..., description="Tugash sanasi: YYYY-MM-DD"), 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Muayyan xodimning ma'lum bir davr uchun davomat hisoboti.
    """
    return await ReportService.get_attendance_report(db, start_date, end_date, user_id=user_id)

# 5. Salary Summary
@router.get("/salary/summary", summary="[Admin/HR] Oylik maosh jamlanmasi")
async def get_salary_summary(month: int = Query(...), year: int = Query(...), db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    return await ReportService.get_salary_summary(db, month, year)

# 6. Detailed Salary Report
@router.get("/salary/detailed", summary="[Admin/HR] Barcha xodimlarning oylik maosh hisoboti")
async def get_detailed_salary(month: int = Query(...), year: int = Query(...), db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    return await ReportService.get_salary_report(db, month, year)

# 7. Employee Salary History
@router.get("/salary/employee/{user_id}", summary="[Admin/HR] Muayyan xodimning maosh tarixi")
async def get_employee_salary_history(user_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    stmt = select(Salary).where(Salary.user_id == user_id).order_by(Salary.year.desc(), Salary.month.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

# 8. Employee Activity Stats
@router.get("/activity/employee/{user_id}", summary="[Admin/HR] Xodim faolligi statistikasi")
async def get_activity_stats(user_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    # Soddalashtirilgan statistika
    return {"user_id": user_id, "status": "active", "stats": "O'rtacha ko'rsatkichlar"}

# 9. Top Performers
@router.get("/activity/top-performers", summary="[Admin/HR] Eng yaxshi ishlagan xodimlar")
async def get_top_performers(db: AsyncSession = Depends(get_db), current_user = Depends(require_role(UserRole.HR_MANAGER))):
    return await ReportService.get_top_performers(db)

# 10, 11, 12. Export (Generic)
@router.get("/export/{format}", summary="[Admin/HR] Hisobotni eksport qilish (CSV/Excel/PDF)")
async def export_report(
    format: str, 
    report_type: str = Query(..., description="users, attendance, salary"), 
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    if format.lower() == "csv":
        csv_data = await ReportService.get_csv_export(db, report_type, month, year)
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    return {"message": f"{report_type} hisoboti {format} formatida tayyorlanmoqda...", "note": "Hozircha faqat CSV to'liq ishlaydi"}
