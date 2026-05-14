"""
Dastlabki ma'lumotlarni yaratish:
- Foydalanuvchilar (admin, hr, employee)
- Davomat (attendance) yozuvlari
- Tranzaksiyalar (bonus, penalty, advance)
- Oylik hisob-kitob (salary)
- Smenalar (shifts)
- Bildirishnomalar (notifications)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, time, date
from app.modules.users.models import User, WorkType
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.salary.models import Transaction, TransactionType, Salary, SalaryStatus
from app.modules.shifts.models import Shift, EmployeeShift
from app.modules.notifications.models import Notification, NotificationType
from app.core.security import hash_password
from app.core.deps import UserRole

# ==================== FOYDALANUVCHILAR ====================
INITIAL_USERS = [
    {
        "phone": "+998901234567",
        "email": "admin@staffflow.uz",
        "first_name": "Shohruh",
        "last_name": "Malikov",
        "password": "Admin@2026",
        "role": UserRole.ADMIN,
        "position": "Sistema Administrator",
        "base_salary": 8000000,
        "expected_monthly_hours": 160,
        "work_start_time": time(8, 30),
        "work_end_time": time(18, 0),
        "avatar_url": "/static/uploads/avatars/admin.jpg",
        "device_id": "admin_device_001"
    },
    {
        "phone": "+998902345678",
        "email": "hr@staffflow.uz",
        "first_name": "Anora",
        "last_name": "Mominova",
        "password": "HRmanager2026",
        "role": UserRole.HR_MANAGER,
        "position": "HR Menedzher",
        "base_salary": 5500000,
        "expected_monthly_hours": 160,
        "work_start_time": time(9, 0),
        "work_end_time": time(18, 0),
        "avatar_url": "/static/uploads/avatars/hrmanager.jpg",
        "device_id": "hr_device_001"
    },
    {
        "phone": "+998903456789",
        "email": "mnurmexrojova@gmail.com",
        "first_name": "Manuchehra",
        "last_name": "Nurmexrojova",
        "password": "Emp@2026",
        "role": UserRole.EMPLOYEE,
        "position": "Backend Developer",
        "base_salary": 4500000,
        "expected_monthly_hours": 160,
        "work_type": WorkType.ONLINE,
        "avatar_url": "/static/uploads/avatars/employee1.jpg",
        "device_id": "emp_device_001"
    },
    {
        "phone": "+998904567890",
        "email": "employee2@staffflow.uz",
        "first_name": "Sardor",
        "last_name": "Mirzaev",
        "password": "Emp@2026",
        "role": UserRole.EMPLOYEE,
        "position": "Frontend Developer",
        "base_salary": 4000000,
        "expected_monthly_hours": 160,
        "work_type": WorkType.ONLINE,
        "avatar_url": "/static/uploads/avatars/employee2.jpg",
        "device_id": "emp_device_002"
    }
]

async def seed_users(db: AsyncSession):
    for data in INITIAL_USERS:
        stmt = select(User).where(User.phone == data["phone"])
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            user = User(
                phone=data["phone"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                hashed_password=hash_password(data["password"]),
                role=data["role"],
                is_active=True,
                base_salary=data["base_salary"],
                expected_monthly_hours=data["expected_monthly_hours"],
                position=data.get("position"),
                work_start_time=data.get("work_start_time", time(9, 0)),
                work_end_time=data.get("work_end_time", time(18, 0)),
                work_type=data.get("work_type", WorkType.ONLINE),
                avatar_url=data.get("avatar_url"),
                device_id=data.get("device_id")
            )
            db.add(user)
    await db.commit()
    print("✅ Users seeded.")

# ==================== SMENALAR ====================
async def seed_shifts(db: AsyncSession):
    shifts_data = [
        {"name": "Ertalabki (08:00 - 17:00)", "start": time(8,0), "end": time(17,0)},
        {"name": "Kungi (10:00 - 19:00)", "start": time(10,0), "end": time(19,0)},
        {"name": "Tungi (20:00 - 05:00)", "start": time(20,0), "end": time(5,0)},
    ]
    
    # Smenalarni yaratish
    for s in shifts_data:
        stmt = select(Shift).where(Shift.name == s["name"])
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            new_s = Shift(name=s["name"], start_time=s["start"], end_time=s["end"])
            db.add(new_s)
    await db.commit()
    print("✅ Shifts seeded.")

# ==================== DAVOMAT ====================
async def seed_attendance_batch(db: AsyncSession, user_id: int, year: int, month: int):
    now = datetime.now()
    if year == now.year and month == now.month:
        max_day = now.day
    else:
        max_day = 28
    
    start_date = date(year, month, 1)
    for d in range(1, max_day + 1):
        curr_date = date(year, month, d)
        if curr_date.weekday() >= 5: continue # Dam olish kunlari

        # Har xil holatlar (kechikish va h.k.)
        late = 0
        if d % 5 == 0: late = 15
        
        att = Attendance(
            user_id=user_id,
            check_in_time=datetime.combine(curr_date, time(9, late)),
            check_out_time=datetime.combine(curr_date, time(18, 0)),
            worked_hours=9.0 - (late/60),
            late_minutes=late,
            check_in_lat=41.2, check_in_lon=69.2,
            status=AttendanceStatus.CHECKED_OUT
        )
        db.add(att)
    await db.commit()

# ==================== MAOSH VA TRANZAKSIYALAR ====================
async def seed_salary_and_trans(db: AsyncSession, user_id: int, year: int, month: int):
    # Tranzaksiya qo'shish
    t = Transaction(user_id=user_id, type=TransactionType.BONUS, amount=200000, reason="Test bonus", date=date(year, month, 10))
    db.add(t)
    
    # Maosh hisoblash (soddalashtirilgan)
    sal = Salary(
        user_id=user_id, month=month, year=year,
        base_salary=4000000, total_worked_hours=160, expected_hours=160,
        bonus_total=200000, penalty_total=0, advance_total=0,
        net_salary=4200000, status=SalaryStatus.PAID
    )
    db.add(sal)
    await db.commit()

# ==================== ASOSIY FUNKSIYA ====================
async def seed_initial_data(db: AsyncSession):
    print("🚀 Seeding test data...")
    await seed_users(db)
    await seed_shifts(db)
    
    # Employee'larni olish
    res = await db.execute(select(User).where(User.role == UserRole.EMPLOYEE))
    employees = res.scalars().all()
    
    now = datetime.now()
    months = [(now.year, now.month), (now.year, now.month - 1 if now.month > 1 else 12)]
    
    for emp in employees:
        for y, m in months:
            await seed_attendance_batch(db, emp.id, y, m)
            await seed_salary_and_trans(db, emp.id, y, m)
        
        # Bildirishnomalar
        n = Notification(user_id=emp.id, title="Xush kelibsiz!", message="Tizimga muvaffaqiyatli kirdingiz", type=NotificationType.SUCCESS)
        db.add(n)
        
    await db.commit()
    print("🎯 All test data seeded successfully.")