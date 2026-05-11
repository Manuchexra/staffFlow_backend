from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql import extract
from datetime import datetime
from fastapi import HTTPException, status
from app.modules.salary.models import Salary, Transaction, TransactionType
from app.modules.users.models import User
from app.modules.attendance.models import Attendance, AttendanceStatus

class SalaryService:
    @staticmethod
    async def calculate_monthly_salary(
        db: AsyncSession,
        user_id: int,
        month: int,
        year: int
    ) -> Salary:
        # 1. Foydalanuvchini tekshirish
        user_stmt = select(User).where(User.id == user_id)
        user = (await db.execute(user_stmt)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 2. Shu oy uchun oldin hisoblangan salary bormi?
        existing = await db.execute(
            select(Salary).where(
                Salary.user_id == user_id,
                Salary.month == month,
                Salary.year == year
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Salary already calculated for this month")
        
        # 3. Ish vaqtlarini hisoblash (attendance)
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year+1, 1, 1)
        else:
            end_date = datetime(year, month+1, 1)
        
        att_stmt = select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.check_in_time >= start_date,
            Attendance.check_in_time < end_date,
            Attendance.status == AttendanceStatus.CHECKED_OUT
        )
        attendances = (await db.execute(att_stmt)).scalars().all()
        total_worked_hours = sum(a.worked_hours for a in attendances)
        
        # 4. Oylik kutilgan soat (user.expected_monthly_hours)
        expected_hours = user.expected_monthly_hours
        
        # 5. Bazaviy maoshni ishlangan soatga proporsional kamaytirish
        if expected_hours > 0:
            salary_base = user.base_salary * (total_worked_hours / expected_hours)
        else:
            salary_base = 0
        
        # 6. Bonus, penalty, advance summalari (shu oy ichidagi)
        trans_stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date < end_date
        )
        transactions = (await db.execute(trans_stmt)).scalars().all()
        bonus_total = sum(t.amount for t in transactions if t.type == TransactionType.BONUS)
        penalty_total = sum(t.amount for t in transactions if t.type == TransactionType.PENALTY)
        advance_total = sum(t.amount for t in transactions if t.type == TransactionType.ADVANCE)
        
        # 7. Net maosh
        net_salary = salary_base + bonus_total - penalty_total - advance_total
        if net_salary < 0:
            net_salary = 0   # maosh manfiy bo‘lishi mumkin emas
        
        # 8. Salary yozuvini yaratish
        salary = Salary(
            user_id=user_id,
            month=month,
            year=year,
            base_salary=user.base_salary,
            total_worked_hours=total_worked_hours,
            expected_hours=expected_hours,
            bonus_total=bonus_total,
            penalty_total=penalty_total,
            advance_total=advance_total,
            net_salary=net_salary,
            status="calculated"
        )
        db.add(salary)
        await db.commit()
        await db.refresh(salary)
        return salary
    
    @staticmethod
    async def get_user_salary_summary(
        db: AsyncSession,
        user_id: int,
        month: int,
        year: int
    ) -> Salary:
        stmt = select(Salary).where(
            Salary.user_id == user_id,
            Salary.month == month,
            Salary.year == year
        )
        salary = (await db.execute(stmt)).scalar_one_or_none()
        if not salary:
            raise HTTPException(status_code=404, detail="Salary not found for given month/year")
        return salary
    
    @staticmethod
    async def add_transaction(
        db: AsyncSession,
        user_id: int,
        trans_type: TransactionType,
        amount: float,
        reason: str = None
    ) -> Transaction:
        # amount musbat bo‘lishi kerak, ishlatishda penalty uchun keyin ayiramiz
        transaction = Transaction(
            user_id=user_id,
            type=trans_type,
            amount=amount,
            reason=reason,
            date=datetime.utcnow()
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction
    
    @staticmethod
    async def get_user_transactions(
        db: AsyncSession,
        user_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> list[Transaction]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        if start_date:
            stmt = stmt.where(Transaction.date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.date < end_date)
        stmt = stmt.order_by(Transaction.date.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_salary_history(db: AsyncSession, user_id: int, limit: int = 12, offset: int = 0) -> List[Salary]:
        stmt = select(Salary).where(Salary.user_id == user_id).order_by(Salary.year.desc(), Salary.month.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_latest_salary(db: AsyncSession, user_id: int) -> Optional[Salary]:
        stmt = select(Salary).where(Salary.user_id == user_id).order_by(Salary.year.desc(), Salary.month.desc()).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_yearly_summary(db: AsyncSession, user_id: int, year: int) -> dict:
        # Salary yig'indisi
        salary_stmt = select(func.sum(Salary.net_salary)).where(
            Salary.user_id == user_id, Salary.year == year
        )
        total_income = (await db.execute(salary_stmt)).scalar() or 0.0

        # Tranzaksiyalar yig'indisi (bonus, penalty, advance)
        bonus_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            extract('year', Transaction.date) == year,
            Transaction.type == TransactionType.BONUS
        )
        total_bonus = (await db.execute(bonus_stmt)).scalar() or 0.0

        penalty_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            extract('year', Transaction.date) == year,
            Transaction.type == TransactionType.PENALTY
        )
        total_penalty = (await db.execute(penalty_stmt)).scalar() or 0.0

        advance_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            extract('year', Transaction.date) == year,
            Transaction.type == TransactionType.ADVANCE
        )
        total_advance = (await db.execute(advance_stmt)).scalar() or 0.0

        return {
            "year": year,
            "total_income": total_income,
            "total_bonus": total_bonus,
            "total_penalty": total_penalty,
            "total_advance": total_advance,
        }