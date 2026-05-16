from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.modules.shifts.models import Shift, EmployeeShift
from app.modules.shifts.schemas import ShiftCreate, ShiftUpdate, EmployeeShiftCreate
from fastapi import HTTPException, status
from datetime import date

class ShiftService:
    # --- Shift Templates (Smena turlari) ---
    
    @staticmethod
    async def create_shift(db: AsyncSession, shift_data: ShiftCreate) -> Shift:
        new_shift = Shift(**shift_data.model_dump())
        db.add(new_shift)
        await db.commit()
        await db.refresh(new_shift)
        return new_shift

    @staticmethod
    async def get_all_shifts(db: AsyncSession):
        stmt = select(Shift)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_shift(db: AsyncSession, shift_id: int, update_data: ShiftUpdate) -> Shift:
        stmt = select(Shift).where(Shift.id == shift_id)
        result = await db.execute(stmt)
        shift = result.scalar_one_or_none()
        if not shift:
            raise HTTPException(status_code=404, detail="Smena topilmadi")
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(shift, field, value)
        
        await db.commit()
        await db.refresh(shift)
        return shift

    # --- Employee Assignments (Xodimlarga biriktirish) ---

    @staticmethod
    async def assign_employee_to_shift(db: AsyncSession, assignment_data: EmployeeShiftCreate) -> EmployeeShift:
        # 1. Tanlangan smena haqida ma'lumot olish
        shift_stmt = select(Shift).where(Shift.id == assignment_data.shift_id)
        shift_res = await db.execute(shift_stmt)
        target_shift = shift_res.scalar_one_or_none()
        if not target_shift:
            raise HTTPException(status_code=404, detail="Smena turi topilmadi")

        # 2. To'qnashuvni tekshirish (Overlap check)
        # selectinload orqali shift ma'lumotlarini ham birga olib kelamiz
        existing_stmt = select(EmployeeShift).options(selectinload(EmployeeShift.shift)).where(
            and_(
                EmployeeShift.user_id == assignment_data.user_id,
                EmployeeShift.date == assignment_data.date
            )
        )
        existing_res = await db.execute(existing_stmt)
        existing_assignments = existing_res.scalars().all()

        for assign in existing_assignments:
            # Vaqt to'qnashuvi mantiqi: (StartA < EndB) AND (EndA > StartB)
            if (target_shift.start_time < assign.shift.end_time) and (target_shift.end_time > assign.shift.start_time):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Vaqt to'qnashuvi! Xodim bu vaqtda '{assign.shift.name}' smenasiga biriktirilgan."
                )

        # 3. Saqlash
        new_assignment = EmployeeShift(**assignment_data.model_dump())
        db.add(new_assignment)
        
        from app.modules.notifications.service import NotificationService
        from app.modules.notifications.models import NotificationType
        
        await NotificationService.send_internal_notification(
            db, assignment_data.user_id, 
            "Yangi smena", 
            f"Sizga {assignment_data.date} kuni uchun '{target_shift.name}' smenasi biriktirildi.",
            NotificationType.INFO
        )
        
        await db.commit()
        # Refresh qilganda ham relationshipni yuklash uchun options ishlatamiz yoki qayta select qilamiz
        stmt = select(EmployeeShift).options(selectinload(EmployeeShift.shift)).where(EmployeeShift.id == new_assignment.id)
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def get_employee_shift_history(db: AsyncSession, user_id: int):
        stmt = select(EmployeeShift).options(selectinload(EmployeeShift.shift)).where(EmployeeShift.user_id == user_id).order_by(EmployeeShift.date.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_all_assignments(db: AsyncSession, date_filter: date = None):
        stmt = select(EmployeeShift).options(selectinload(EmployeeShift.shift))
        if date_filter:
            stmt = stmt.where(EmployeeShift.date == date_filter)
        result = await db.execute(stmt)
        return result.scalars().all()
