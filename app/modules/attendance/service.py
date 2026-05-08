from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from fastapi import HTTPException, status
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.users.models import User
from app.modules.attendance.geofence import is_within_geofence

class AttendanceService:
    @staticmethod
    async def check_in(db: AsyncSession, user_id: int, lat: float, lon: float):
        if not is_within_geofence(lat, lon):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Outside allowed geofence")
        stmt = select(Attendance).where(Attendance.user_id == user_id, Attendance.status == AttendanceStatus.CHECKED_IN)
        active = (await db.execute(stmt)).scalar_one_or_none()
        if active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already checked in")
        user_stmt = select(User).where(User.id == user_id)
        user = (await db.execute(user_stmt)).scalar_one()
        now = datetime.now()
        scheduled_start = datetime.combine(now.date(), user.work_start_time)
        late_minutes = int((now - scheduled_start).total_seconds() / 60) if now > scheduled_start else 0
        attendance = Attendance(
            user_id=user_id,
            check_in_time=now,
            check_in_lat=lat,
            check_in_lon=lon,
            late_minutes=late_minutes,
            status=AttendanceStatus.CHECKED_IN
        )
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance

    @staticmethod
    async def check_out(db: AsyncSession, user_id: int, lat: float, lon: float):
        if not is_within_geofence(lat, lon):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Outside allowed geofence")
        stmt = select(Attendance).where(Attendance.user_id == user_id, Attendance.status == AttendanceStatus.CHECKED_IN).order_by(Attendance.check_in_time.desc())
        record = (await db.execute(stmt)).scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active check-in")
        now = datetime.now()
        worked_seconds = (now - record.check_in_time).total_seconds()
        record.check_out_time = now
        record.check_out_lat = lat
        record.check_out_lon = lon
        record.worked_hours = round(worked_seconds / 3600, 2)
        record.status = AttendanceStatus.CHECKED_OUT
        await db.commit()
        await db.refresh(record)
        return record