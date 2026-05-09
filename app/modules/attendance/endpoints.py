from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user, require_role, UserRole
from app.modules.users.models import User
from app.modules.attendance.schemas import CheckInRequest, CheckOutRequest, AttendanceResponse
from app.modules.attendance.service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/check-in", response_model=AttendanceResponse, summary="[Employee] Ishga kelishni qayd etish")
async def check_in(request: CheckInRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.EMPLOYEE))):
    attendance = await AttendanceService.check_in(db, current_user.id, request.latitude, request.longitude)
    return attendance

@router.post("/check-out", response_model=AttendanceResponse, summary="[Employee] Ishdan ketishni qayd etish")
async def check_out(request: CheckOutRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.EMPLOYEE))):
    attendance = await AttendanceService.check_out(db, current_user.id, request.latitude, request.longitude)
    return attendance

@router.get("/my-attendance", summary="[Employee] O'z davomatini ko'rish")
async def get_my_attendance(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import select
    from app.modules.attendance.models import Attendance
    stmt = select(Attendance).where(Attendance.user_id == current_user.id).order_by(Attendance.check_in_time.desc())
    result = await db.execute(stmt)
    return result.scalars().all()