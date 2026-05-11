from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Enum as SQLEnum, DateTime, Time, Float, Integer
from datetime import datetime, time
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    EMPLOYEE = "employee"

class WorkType(str, enum.Enum):
    ONLINE = "online"   # ofisda, geofence talab qilinadi
    OFFLINE = "offline" # masofaviy, attendance shart emas

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(75))
    last_name: Mapped[str] = mapped_column(String(75))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    work_type: Mapped[WorkType] = mapped_column(SQLEnum(WorkType), default=WorkType.ONLINE)

    work_start_time: Mapped[time] = mapped_column(Time, default=time(9,0,0))
    work_end_time: Mapped[time] = mapped_column(Time, default=time(18,0,0))
    
    base_salary: Mapped[float] = mapped_column(Float, default=0.0)          # oylik bazaviy maosh (so'mda)
    expected_monthly_hours: Mapped[float] = mapped_column(Float, default=160.0)  # oylik kutilgan ish soati

    avatar_url: Mapped[str] = mapped_column(String, nullable=True)   # rasm URL yoki base64
    position: Mapped[str] = mapped_column(String(100), nullable=True)  
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)  # mobil qurilma ID
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
