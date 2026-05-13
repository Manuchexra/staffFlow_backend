from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CheckInRequest(BaseModel):
    latitude: float
    longitude: float
    ssid: str
    bssid: str

class CheckOutRequest(BaseModel):
    latitude: float
    longitude: float
    ssid: str
    bssid: str

class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime]
    worked_hours: float
    late_minutes: int
    status: str