from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_role, UserRole
from app.modules.shifts.schemas import ShiftCreate, ShiftResponse, ShiftUpdate, EmployeeShiftCreate, EmployeeShiftResponse
from app.modules.shifts.service import ShiftService
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/shifts", tags=["Shift Management"])

# --- Smena turlarini boshqarish ---

@router.post("/", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED, summary="[HR] Yangi smena turi yaratish")
async def create_shift(
    shift_data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await ShiftService.create_shift(db, shift_data)

@router.get("/", response_model=List[ShiftResponse], summary="[HR/Auth] Barcha smena turlarini ko'rish")
async def list_shifts(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.EMPLOYEE)) # Hamman ko'ra oladi
):
    return await ShiftService.get_all_shifts(db)

@router.patch("/{shift_id}", response_model=ShiftResponse, summary="[HR] Smena turini tahrirlash")
async def update_shift(
    shift_id: int,
    update_data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await ShiftService.update_shift(db, shift_id, update_data)

# --- Xodimlarga smenalarni biriktirish ---

@router.post("/assign", response_model=EmployeeShiftResponse, summary="[HR] Xodimni smenaga biriktirish")
async def assign_employee(
    assignment_data: EmployeeShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    """
    Xodimni ma'lum bir kunda ma'lum bir smenaga biriktiradi. 
    Vaqtlar to'qnashuvi avtomatik tekshiriladi.
    """
    return await ShiftService.assign_employee_to_shift(db, assignment_data)

@router.get("/assignments", response_model=List[EmployeeShiftResponse], summary="[HR] Barcha biriktirilgan smenalarni ko'rish")
async def list_assignments(
    target_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await ShiftService.get_all_assignments(db, target_date)

@router.get("/history/{user_id}", response_model=List[EmployeeShiftResponse], summary="[HR] Xodimning smenalar tarixi")
async def get_history(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(UserRole.HR_MANAGER))
):
    return await ShiftService.get_employee_shift_history(db, user_id)
