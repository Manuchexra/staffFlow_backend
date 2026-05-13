from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Time, Date, ForeignKey, DateTime, Integer
from datetime import time, date, datetime
from app.database import Base

class Shift(Base):
    __tablename__ = "shifts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False) # Masalan: "Ertalabki smena"
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Assignments bilan bog'liqlik
    assignments = relationship("EmployeeShift", back_populates="shift", cascade="all, delete-orphan")

class EmployeeShift(Base):
    __tablename__ = "employee_shifts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Bog'liqliklar
    shift = relationship("Shift", back_populates="assignments")
    user = relationship("app.modules.users.models.User") # Foydalanuvchi ma'lumotlari uchun
