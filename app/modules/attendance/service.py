from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from fastapi import HTTPException, status
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.users.models import User
from app.modules.attendance.geofence import is_within_geofence

from app.config import settings
class AttendanceService:
    @staticmethod
    async def check_in(db: AsyncSession, user_id: int, lat: float, lon: float, ssid: str, bssid: str):
        # Yo WiFi mos kelishi kerak, yoki Geofence (GPS) hududida bo'lishi kerak
        is_wifi_ok = (ssid == settings.OFFICE_SSID and bssid.upper() == settings.OFFICE_BSSID.upper())
        is_gps_ok = is_within_geofence(lat, lon)

        print(f"DEBUG: WiFi={is_wifi_ok} (Got: {ssid}/{bssid}, Expected: {settings.OFFICE_SSID}/{settings.OFFICE_BSSID})")
        print(f"DEBUG: GPS={is_gps_ok} (Lat: {lat}, Lon: {lon})")

        if not is_wifi_ok and not is_gps_ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Davomat uchun yo ofis WiFi-siga ulaning, yoki ofis hududida (GPS) bo'ling."
            )

        stmt = select(Attendance).where(Attendance.user_id == user_id, Attendance.status == AttendanceStatus.CHECKED_IN).order_by(Attendance.check_in_time.desc())
        result = await db.execute(stmt)
        active = result.scalars().first()
        
        if active:
            return active
        
        user_stmt = select(User).where(User.id == user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one()
        
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
    async def check_out(db: AsyncSession, user_id: int, lat: float, lon: float, ssid: str, bssid: str):
        # Yo WiFi mos kelishi kerak, yoki Geofence (GPS) hududida bo'lishi kerak
        is_wifi_ok = (ssid == settings.OFFICE_SSID and bssid.upper() == settings.OFFICE_BSSID.upper())
        is_gps_ok = is_within_geofence(lat, lon)

        if not is_wifi_ok and not is_gps_ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Davomat uchun yo ofis WiFi-siga ulaning, yoki ofis hududida (GPS) bo'ling."
            )
        
        stmt = select(Attendance).where(Attendance.user_id == user_id, Attendance.status == AttendanceStatus.CHECKED_IN).order_by(Attendance.check_in_time.desc())
        result = await db.execute(stmt)
        record = result.scalars().first()
        
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