from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, Float, Integer, String, Enum
from datetime import datetime
from app.database import Base
import enum

class TransactionType(str, enum.Enum):
    BONUS = "bonus"
    PENALTY = "penalty"
    ADVANCE = "advance"

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount: Mapped[float] = mapped_column(Float)          # musbat (bonus/advance) yoki manfiy (penalty) qilib ishlatsa bo‘ladi, lekin alohida maydon
    reason: Mapped[str] = mapped_column(String(255), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_paid: Mapped[bool] = mapped_column(default=False)   # avans uchun to‘langanmi

class SalaryStatus(str, enum.Enum):
    CALCULATED = "calculated"
    PAID = "paid"

class Salary(Base):
    __tablename__ = "salaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    month: Mapped[int] = mapped_column(Integer)      # 1-12
    year: Mapped[int] = mapped_column(Integer)
    base_salary: Mapped[float] = mapped_column(Float)
    total_worked_hours: Mapped[float] = mapped_column(Float)
    expected_hours: Mapped[float] = mapped_column(Float)
    bonus_total: Mapped[float] = mapped_column(Float, default=0.0)
    penalty_total: Mapped[float] = mapped_column(Float, default=0.0)
    advance_total: Mapped[float] = mapped_column(Float, default=0.0)
    net_salary: Mapped[float] = mapped_column(Float)
    status: Mapped[SalaryStatus] = mapped_column(Enum(SalaryStatus), default=SalaryStatus.CALCULATED)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)