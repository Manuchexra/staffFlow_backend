"""
Dastlabki ma'lumotlarni yaratish:
- Foydalanuvchilar (admin, hr, employee)
- Davomat (attendance) yozuvlari
- Tranzaksiyalar (bonus, penalty, advance)
- Oylik hisob-kitob (salary)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, time
from app.modules.users.models import User
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.salary.models import Transaction, TransactionType, Salary, SalaryStatus
from app.core.security import hash_password
from app.core.deps import UserRole

# ==================== FOYDALANUVCHILAR ====================
INITIAL_USERS = [
    {
        "phone": "+998901234567",
        "email": "admin@staffflow.uz",
        "full_name": "Admin User",
        "password": "admin123",
        "role": UserRole.ADMIN,
        "base_salary": 0,
        "expected_monthly_hours": 160
    },
    {
        "phone": "+998902345678",
        "email": "hr@staffflow.uz",
        "full_name": "HR Manager",
        "password": "hr123",
        "role": UserRole.HR_MANAGER,
        "base_salary": 5000000,
        "expected_monthly_hours": 160
    },
    {
        "phone": "+998903456789",
        "email": "employee@staffflow.uz",
        "full_name": "Regular Employee",
        "password": "emp123",
        "role": UserRole.EMPLOYEE,
        "base_salary": 3000000,
        "expected_monthly_hours": 160
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
                full_name=data["full_name"],
                hashed_password=hash_password(data["password"]),
                role=data["role"],
                is_active=True,
                base_salary=data["base_salary"],
                expected_monthly_hours=data["expected_monthly_hours"]
            )
            db.add(user)
            print(f"✅ Created user: {data['full_name']} ({data['role'].value})")
    await db.commit()

# ==================== ATTENDANCE ====================
async def seed_attendance(db: AsyncSession, user_id: int, year: int, month: int):
    """
    Berilgan oy uchun ish kunlarida (dushanba–juma) check-in/out yozuvlarini yaratadi.
    Ish vaqti: 09:00 – 18:00, kechikish va erta ketish bilan aralashtiriladi.
    """
    now = datetime.now()
    # Agar joriy oy va yil bo'lsa, faqat o‘tgan kunlarni yaratish
    if year == now.year and month == now.month:
        max_day = now.day - 1
    else:
        max_day = 30  # soddalashtirish

    start_date = datetime(year, month, 1)
    for day in range(1, max_day + 1):
        current_date = start_date + timedelta(days=day-1)
        # Faqat ish kunlari (dushanba=0, yakshanba=6)
        if current_date.weekday() >= 5:
            continue

        # Check-in: 9:00 + kechikish (0-30 min)
        check_in_time = datetime(current_date.year, current_date.month, current_date.day, 9, 0, 0)
        late_minutes = 0
        if day % 3 == 0:  # har 3-kuni 10 daqiqa kechikish
            check_in_time += timedelta(minutes=10)
            late_minutes = 10
        elif day % 5 == 0:  # har 5-kuni 20 daqiqa kech
            check_in_time += timedelta(minutes=20)
            late_minutes = 20

        # Check-out: 18:00 +/- 15 min
        check_out_time = datetime(current_date.year, current_date.month, current_date.day, 18, 0, 0)
        if day % 2 == 0:  # juft kunlari erta ketish (17:45)
            check_out_time -= timedelta(minutes=15)
        elif day % 7 == 0:  # hafta oxiri oldidan qo'shimcha 15 min kech
            check_out_time += timedelta(minutes=15)

        worked_seconds = (check_out_time - check_in_time).total_seconds()
        worked_hours = round(worked_seconds / 3600, 2)

        attendance = Attendance(
            user_id=user_id,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            worked_hours=worked_hours,
            late_minutes=late_minutes,
            check_in_lat=41.311081,
            check_in_lon=69.240562,
            check_out_lat=41.311081,
            check_out_lon=69.240562,
            status=AttendanceStatus.CHECKED_OUT
        )
        db.add(attendance)
    await db.commit()
    print(f"✅ Created attendance records for user {user_id} for {year}-{month}")

# ==================== TRANSACTIONS ====================
async def seed_transactions(db: AsyncSession, user_id: int, year: int, month: int):
    # Bonus, penalty, advance misollar
    transactions = [
        {"type": TransactionType.BONUS, "amount": 200000, "reason": "Yaxshi ish natijasi", "date_offset": 5},
        {"type": TransactionType.BONUS, "amount": 50000, "reason": "Mijozdan minnatdorchilik", "date_offset": 12},
        {"type": TransactionType.PENALTY, "amount": 50000, "reason": "Kech kelish", "date_offset": 3},
        {"type": TransactionType.PENALTY, "amount": 30000, "reason": "Hisobot topshirmaslik", "date_offset": 18},
        {"type": TransactionType.ADVANCE, "amount": 500000, "reason": "Avans (15-kun)", "date_offset": 15},
    ]
    start_date = datetime(year, month, 1)
    for t in transactions:
        trans_date = start_date + timedelta(days=t["date_offset"]-1)
        # Mavjudlikni tekshirish (oddiy: shu user, shu kun, shu turdagi tranzaksiya bormi? Soddalik uchun takrorlamaymiz)
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.type == t["type"],
            Transaction.date == trans_date
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            trans = Transaction(
                user_id=user_id,
                type=t["type"],
                amount=t["amount"],
                reason=t["reason"],
                date=trans_date,
                is_paid=(t["type"] == TransactionType.ADVANCE)  # avans to‘langan deb belgilaymiz
            )
            db.add(trans)
    await db.commit()
    print(f"✅ Created transactions for user {user_id} for {year}-{month}")

# ==================== SALARY ====================
async def seed_salary(db: AsyncSession, user_id: int, year: int, month: int):
    # Oldin salary mavjudligini tekshiramiz
    stmt = select(Salary).where(
        Salary.user_id == user_id, Salary.year == year, Salary.month == month
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        print(f"ℹ️ Salary already exists for user {user_id} {year}-{month}")
        return

    # User ma'lumotlarini olish
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
    # Attendance yig'indisi
    att_stmt = select(Attendance).where(
        Attendance.user_id == user_id,
        Attendance.check_in_time >= datetime(year, month, 1),
        Attendance.check_in_time < (
            datetime(year+1, 1, 1) if month==12 else datetime(year, month+1, 1)
        )
    )
    attendances = (await db.execute(att_stmt)).scalars().all()
    total_worked_hours = sum(a.worked_hours for a in attendances)
    expected_hours = user.expected_monthly_hours
    salary_base = user.base_salary * (total_worked_hours / expected_hours) if expected_hours > 0 else 0

    # Tranzaksiyalar yig'indisi
    trans_stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.date >= datetime(year, month, 1),
        Transaction.date < (datetime(year+1, 1, 1) if month==12 else datetime(year, month+1, 1))
    )
    transactions = (await db.execute(trans_stmt)).scalars().all()
    bonus_total = sum(t.amount for t in transactions if t.type == TransactionType.BONUS)
    penalty_total = sum(t.amount for t in transactions if t.type == TransactionType.PENALTY)
    advance_total = sum(t.amount for t in transactions if t.type == TransactionType.ADVANCE)

    net_salary = salary_base + bonus_total - penalty_total - advance_total
    if net_salary < 0:
        net_salary = 0

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
        status=SalaryStatus.CALCULATED
    )
    db.add(salary)
    await db.commit()
    print(f"✅ Created salary for user {user_id} {year}-{month}: net = {net_salary} so'm")

# ==================== ASOSIY SEED FUNKSIYASI ====================
async def seed_initial_data(db: AsyncSession):
    # 1. Foydalanuvchilar
    await seed_users(db)

    # 2. Employee ID sini olish
    emp_stmt = select(User).where(User.phone == "+998903456789")
    employee = (await db.execute(emp_stmt)).scalar_one_or_none()
    if not employee:
        print("⚠️ Employee not found, skipping attendance/transactions/salary seed")
        return

    now = datetime.now()
    year, month = now.year, now.month

    # 3. Attendance (joriy oy uchun, faqat o'tgan kunlar)
    await seed_attendance(db, employee.id, year, month)

    # 4. Transactions
    await seed_transactions(db, employee.id, year, month)

    # 5. Salary hisoblash
    await seed_salary(db, employee.id, year, month)