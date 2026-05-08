from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TransactionTypeEnum(str, Enum):
    BONUS = "bonus"
    PENALTY = "penalty"
    ADVANCE = "advance"

class TransactionCreate(BaseModel):
    type: TransactionTypeEnum
    amount: float = Field(..., gt=0)
    reason: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: TransactionTypeEnum
    amount: float
    reason: Optional[str]
    date: datetime
    is_paid: bool

class SalaryCalculateRequest(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2030)

class SalarySummaryResponse(BaseModel):
    user_id: int
    full_name: str
    month: int
    year: int
    base_salary: float
    total_worked_hours: float
    expected_hours: float
    bonus_total: float
    penalty_total: float
    advance_total: float
    net_salary: float
    status: str
    calculated_at: datetime

class SalaryListResponse(BaseModel):
    salaries: List[SalarySummaryResponse]