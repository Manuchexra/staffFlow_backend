from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, Float, Integer, Enum
from datetime import datetime
from app.database import Base
import enum

class AttendanceStatus(str, enum.Enum):
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"

class Attendance(Base):
    __tablename__ = "attendances"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    check_in_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    check_out_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    worked_hours: Mapped[float] = mapped_column(Float, default=0.0)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    check_in_lat: Mapped[float] = mapped_column(Float)
    check_in_lon: Mapped[float] = mapped_column(Float)
    check_out_lat: Mapped[float] = mapped_column(Float, nullable=True)
    check_out_lon: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), default=AttendanceStatus.CHECKED_IN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)