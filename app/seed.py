"""
Dastlabki ma'lumotlarni yaratish:
- Foydalanuvchilar (admin, hr, employee)
- Davomat (attendance) yozuvlari
- Tranzaksiyalar (bonus, penalty, advance)
- Oylik hisob-kitob (salary)
- Smenalar (shifts)
- Bildirishnomalar (notifications)
- RBAC (Roles & Permissions)
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
from app.modules.rbac.models import Role, Permission
from app.modules.rbac.service import RBACService

# ==================== RBAC (ROLLAR VA RUXSATLAR) ====================
INITIAL_PERMISSIONS = [
    {"name": "user:read", "description": "Xodimlarni ko'rish"},
    {"name": "user:create", "description": "Yangi xodim qo'shish"},
    {"name": "user:update", "description": "Xodim ma'lumotlarini tahrirlash"},
    {"name": "user:delete", "description": "Xodimni o'chirish"},
    {"name": "report:read", "description": "Hisobotlarni ko'rish"},
    {"name": "report:export", "description": "Hisobotlarni CSV/PDF eksport qilish"},
    {"name": "attendance:manage", "description": "Davomatni boshqarish"},
    {"name": "salary:calculate", "description": "Maoshni hisoblash"},
    {"name": "shift:manage", "description": "Smenalarni boshqarish"},
    {"name": "notification:send", "description": "Bildirishnoma yuborish"},
]

async def seed_rbac(db: AsyncSession):
    # 1. Permissionlarni yaratish
    permissions_map = {}
    for p_data in INITIAL_PERMISSIONS:
        stmt = select(Permission).where(Permission.name == p_data["name"])
        res = await db.execute(stmt)
        p = res.scalar_one_or_none()
        if not p:
            p = Permission(**p_data)
            db.add(p)
            await db.flush()
        permissions_map[p.name] = p.id
    
    # 2. Rollarni yaratish va ruxsatlarni biriktirish
    roles_data = [
        {
            "name": "HR_MANAGER",
            "description": "Barcha HR amallari",
            "permissions": ["user:read", "user:create", "user:update", "report:read", "report:export", "attendance:manage", "salary:calculate", "shift:manage", "notification:send"]
        },
        {
            "name": "EMPLOYEE",
            "description": "Oddiy xodim ruxsatlari",
            "permissions": ["user:read"]
        }
    ]

    for r_data in roles_data:
        stmt = select(Role).where(Role.name == r_data["name"])
        res = await db.execute(stmt)
        role = res.scalar_one_or_none()
        if not role:
            role = Role(name=r_data["name"], description=r_data["description"])
            db.add(role)
            await db.flush()
        
        # Ruxsatlarni biriktirish
        role_p_ids = [permissions_map[p_name] for p_name in r_data["permissions"]]
        await RBACService.assign_permissions_to_role(db, role.id, role_p_ids)

    await db.commit()
    print("✅ RBAC (Roles & Permissions) seeded.")

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
        "phone": "+998909876543",
        "email": "admin2@staffflow.uz",
        "first_name": "Diyor",
        "last_name": "Rustamov",
        "password": "Admin@2026",
        "role": UserRole.ADMIN,
        "position": "Yordamchi Administrator",
        "base_salary": 7500000,
        "expected_monthly_hours": 160,
        "work_start_time": time(8, 30),
        "work_end_time": time(18, 0),
        "avatar_url": "/static/uploads/avatars/admin2.jpg",
        "device_id": "admin_device_002"
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
    },
    {
        "phone": "+998905678901",
        "email": "hr2@staffflow.uz",
        "first_name": "Madina",
        "last_name": "Sultonova",
        "password": "HRmanager2026",
        "role": UserRole.HR_MANAGER,
        "position": "Junior HR Specialist",
        "base_salary": 4500000,
        "expected_monthly_hours": 160,
        "work_start_time": time(9, 0),
        "work_end_time": time(18, 0),
        "avatar_url": "/static/uploads/avatars/hrmanager2.jpg",
        "device_id": "hr_device_002"
    },
    {
        "phone": "+998906789012",
        "email": "employee3@staffflow.uz",
        "first_name": "Jasur",
        "last_name": "Karimov",
        "password": "Emp@2026",
        "role": UserRole.EMPLOYEE,
        "position": "Mobile Developer",
        "base_salary": 4800000,
        "expected_monthly_hours": 160,
        "work_type": WorkType.ONLINE,
        "avatar_url": "/static/uploads/avatars/employee3.jpg",
        "device_id": "emp_device_003"
    },
    {
        "phone": "+998907890123",
        "email": "employee4@staffflow.uz",
        "first_name": "Kamola",
        "last_name": "Alieva",
        "password": "Emp@2026",
        "role": UserRole.EMPLOYEE,
        "position": "QA Engineer",
        "base_salary": 3800000,
        "expected_monthly_hours": 160,
        "work_type": WorkType.ONLINE,
        "avatar_url": "/static/uploads/avatars/employee4.jpg",
        "device_id": "emp_device_004"
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
    await seed_rbac(db)
    await seed_users(db)
    await seed_shifts(db)
    
    # Employee'larni olish
    res = await db.execute(select(User).where(User.role == UserRole.EMPLOYEE))
    employees = res.scalars().all()
    
    # HR ni olish va unga RBAC rolini biriktirish
    hr_res = await db.execute(select(User).where(User.role == UserRole.HR_MANAGER))
    hr_users = hr_res.scalars().all()
    role_res = await db.execute(select(Role).where(Role.name == "HR_MANAGER"))
    hr_role = role_res.scalar_one_or_none()
    if hr_role:
        for hr_user in hr_users:
            await RBACService.assign_roles_to_user(db, hr_user.id, [hr_role.id])

    now = datetime.now()
    months = [(now.year, now.month), (now.year, now.month - 1 if now.month > 1 else 12)]
    
    for emp in employees:
        # Har bir xodimga EMPLOYEE rolini berish
        role_res = await db.execute(select(Role).where(Role.name == "EMPLOYEE"))
        emp_role = role_res.scalar_one_or_none()
        if emp_role:
            await RBACService.assign_roles_to_user(db, emp.id, [emp_role.id])

        for y, m in months:
            await seed_attendance_batch(db, emp.id, y, m)
            await seed_salary_and_trans(db, emp.id, y, m)
        
        # Bildirishnomalar
        n = Notification(user_id=emp.id, title="Xush kelibsiz!", message="Tizimga muvaffaqiyatli kirdingiz", type=NotificationType.SUCCESS)
        db.add(n)
        
    await db.commit()
    print("🎯 All test data seeded successfully.")