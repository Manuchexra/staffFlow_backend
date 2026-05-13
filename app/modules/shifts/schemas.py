from pydantic import BaseModel
from typing import Optional, List
from datetime import time, date, datetime

class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    description: Optional[str] = None

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    description: Optional[str] = None

class ShiftResponse(ShiftBase):
    id: int

    class Config:
        from_attributes = True

class EmployeeShiftCreate(BaseModel):
    user_id: int
    shift_id: int
    date: date

class EmployeeShiftResponse(BaseModel):
    id: int
    user_id: int
    shift_id: int
    date: date
    created_at: datetime
    shift: ShiftResponse

    class Config:
        from_attributes = True

class ShiftHistoryResponse(BaseModel):
    user_id: int
    assignments: List[EmployeeShiftResponse]
