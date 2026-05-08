from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role, UserRole
from app.modules.users.models import User
from app.modules.salary.schemas import (
    TransactionCreate, TransactionResponse,
    SalaryCalculateRequest, SalarySummaryResponse, SalaryListResponse
)
from app.modules.salary.service import SalaryService
from app.modules.salary.models import TransactionType, Salary, Transaction
from datetime import datetime

router = APIRouter(prefix="/salary", tags=["Salary"])

# ========== Xodim o‘z maoshini ko‘rishi ==========
@router.get("/my", response_model=SalarySummaryResponse)
async def get_my_salary(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    salary = await SalaryService.get_user_salary_summary(db, current_user.id, month, year)
    # user_info ni to‘ldirish uchun
    return SalarySummaryResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        month=salary.month,
        year=salary.year,
        base_salary=salary.base_salary,
        total_worked_hours=salary.total_worked_hours,
        expected_hours=salary.expected_hours,
        bonus_total=salary.bonus_total,
        penalty_total=salary.penalty_total,
        advance_total=salary.advance_total,
        net_salary=salary.net_salary,
        status=salary.status.value,
        calculated_at=salary.calculated_at
    )

# ========== Hisoblash (faqat admin/HR) ==========
@router.post("/calculate", response_model=SalarySummaryResponse)
async def calculate_salary(
    req: SalaryCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.HR_MANAGER))  # HR yoki admin
):
    # Agar current_user admin yoki HR bo‘lsa, qaysi user uchun hisoblash kerak? 
    # Keling, request bodyga user_id qo‘shaylik yoki o‘ziga hisoblasin.
    # SRS da HR boshqaradi. Shuning uchun endpointga user_id qo‘shamiz.
    # Keling, query parametr sifatida user_id olamiz.
    raise HTTPException(status_code=400, detail="Use /calculate/{user_id} endpoint")

@router.post("/calculate/{user_id}", response_model=SalarySummaryResponse)
async def calculate_salary_for_user(
    user_id: int,
    req: SalaryCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.HR_MANAGER))
):
    salary = await SalaryService.calculate_monthly_salary(db, user_id, req.month, req.year)
    # user nomini olish
    from sqlalchemy import select
    user_stmt = select(User).where(User.id == user_id)
    user = (await db.execute(user_stmt)).scalar_one()
    return SalarySummaryResponse(
        user_id=user.id,
        full_name=user.full_name,
        month=salary.month,
        year=salary.year,
        base_salary=salary.base_salary,
        total_worked_hours=salary.total_worked_hours,
        expected_hours=salary.expected_hours,
        bonus_total=salary.bonus_total,
        penalty_total=salary.penalty_total,
        advance_total=salary.advance_total,
        net_salary=salary.net_salary,
        status=salary.status.value,
        calculated_at=salary.calculated_at
    )

# ========== Transaction CRUD (Admin/HR) ==========
@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    user_id: int,
    trans_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.HR_MANAGER))
):
    ttype = TransactionType(trans_data.type.value)
    transaction = await SalaryService.add_transaction(
        db, user_id, ttype, trans_data.amount, trans_data.reason
    )
    return transaction

@router.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.HR_MANAGER))
):
    if user_id is None:
        # agar admin bo‘lsa, barcha transactionlarni olish? kerak bo‘lsa
        user_id = current_user.id if current_user.role == UserRole.EMPLOYEE else None
        if user_id is None:
            # admin hamma transactionlarni ko‘rsin
            from app.modules.salary.models import Transaction
            stmt = select(Transaction).order_by(Transaction.date.desc())
            result = await db.execute(stmt)
            return result.scalars().all()
    transactions = await SalaryService.get_user_transactions(db, user_id)
    return transactions

# Xodim o‘z transactionlarini ko‘rishi
@router.get("/my/transactions", response_model=list[TransactionResponse])
async def get_my_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = await SalaryService.get_user_transactions(db, current_user.id)
    return transactions

# Admin/HR uchun barcha xodimlarning oyliklari ro‘yxati
@router.get("/all", response_model=SalaryListResponse)
async def get_all_salaries(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.HR_MANAGER))
):
    from sqlalchemy import select
    stmt = select(Salary).where(Salary.month == month, Salary.year == year)
    result = await db.execute(stmt)
    salaries = result.scalars().all()
    # user nomlarini qo‘shish
    items = []
    for sal in salaries:
        user_stmt = select(User).where(User.id == sal.user_id)
        user = (await db.execute(user_stmt)).scalar_one()
        items.append(SalarySummaryResponse(
            user_id=user.id,
            full_name=user.full_name,
            month=sal.month,
            year=sal.year,
            base_salary=sal.base_salary,
            total_worked_hours=sal.total_worked_hours,
            expected_hours=sal.expected_hours,
            bonus_total=sal.bonus_total,
            penalty_total=sal.penalty_total,
            advance_total=sal.advance_total,
            net_salary=sal.net_salary,
            status=sal.status.value,
            calculated_at=sal.calculated_at
        ))
    return SalaryListResponse(salaries=items)