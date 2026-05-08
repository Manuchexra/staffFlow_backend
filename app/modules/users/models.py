from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Enum as SQLEnum, DateTime, Time, Float, Integer
from datetime import datetime, time
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    EMPLOYEE = "employee"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(default=True)
    work_start_time: Mapped[time] = mapped_column(Time, default=time(9,0,0))
    work_end_time: Mapped[time] = mapped_column(Time, default=time(18,0,0))
    # Yangi: ish haqi sozlamalari
    base_salary: Mapped[float] = mapped_column(Float, default=0.0)          # oylik bazaviy maosh (so'mda)
    expected_monthly_hours: Mapped[float] = mapped_column(Float, default=160.0)  # oylik kutilgan ish soati
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)