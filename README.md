# StaffFlow Backend API

StaffFlow — avtomatlashtirilgan davomat va moliya boshqaruv tizimi backend qismi.  
Ushbu repository 1-bosqich (JWT autentifikatsiya) va 2-bosqich (GPS va geofence asosida check-in/out) funksiyalarini o‘z ichiga oladi.

## 📦 Texnologiyalar

- **FastAPI** — asosiy web framework
- **PostgreSQL** — asosiy ma’lumotlar bazasi
- **Redis** — rate limiting va session boshqaruvi
- **SQLAlchemy 2.x** (async) — ORM
- **JWT** — token autentifikatsiyasi
- **Docker & Docker Compose** — konteynerizatsiya
- **Python 3.12+**

## 🚀 Ishga tushirish (Docker)

```bash
# .env faylini sozlang (agar mavjud bo'lmasa)
cp .env.example .env

# Docker orqali ishga tushiring
docker-compose up -d --build
```

Dastur ishga tushgach, quyidagi manzillar orqali boshqarishingiz mumkin:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **pgAdmin**: [http://localhost:5050](http://localhost:5050) (Baza boshqaruvi)

### pgAdmin login:
- **Email**: `admin@staffflow.local`
- **Password**: `admin123`

---

## 📡 API Foydalanish (Qo‘llanma)

### 1. Autentifikatsiya (JWT)
Tizimga kirish va token olish uchun `/api/v1/auth/login` endpointiga so‘rov yuboring.

**Request:**
`POST /api/v1/auth/login`
```json
{
  "identifier": "somebody@gmail.com",
  "password": "somebody123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer"
}
```

> [!IMPORTANT]
> Keyingi barcha so‘rovlarda ushbu `access_token`ni **Authorization: Bearer <token>** headeri orqali yuborish shart.

---

### 2. Davomat (Attendance)
Davomat faqat geofencing (belgilangan radius) ichida ishlaydi. Koordinatalarni `.env` orqali o'zgartirish mumkin.

#### Check-in (Ishga kelish)
**Request:**
`POST /api/v1/attendance/check-in`
```json
{
  "latitude": 41.311081,
  "longitude": 69.240562
}
```

#### Check-out (Ishdan ketish)
**Request:**
`POST /api/v1/attendance/check-out`
```json
{
  "latitude": 41.311081,
  "longitude": 69.240562
}
```

#### Mening davomatim
`GET /api/v1/attendance/my-attendance`

---

### 3. Maosh va Moliya (Salary)
Oylik hisob-kitoblar va bonus/jarimalarni boshqarish.

#### Xodim uchun:
- **Oylikni ko‘rish**: `GET /api/v1/salary/my?month=5&year=2026`
- **O‘z bonus/jarimalarini ko‘rish**: `GET /api/v1/salary/my/transactions`

#### Admin/HR uchun:
- **Oylik hisoblash (User uchun)**: `POST /api/v1/salary/calculate/{user_id}`
  - Request body: `{"month": 5, "year": 2026}`
- **Bonus/Jarima/Avans qo‘shish**: `POST /api/v1/salary/transactions?user_id={user_id}`
  - Request body:
    ```json
    {
      "type": "bonus", 
      "amount": 500000,
      "reason": "Yaxshi natija uchun"
    }
    ```
  - `type`: `bonus`, `penalty`, `advance`.
#### Barcha oyliklarni ko‘rishi
`GET /api/v1/salary/all?month=5&year=2026`

---

### 4. Foydalanuvchilarni boshqarish (Admin faqat)
Tizimga yangi xodimlarni qo‘shish va ro‘yxatni ko‘rish.

- **Yangi xodim yaratish**: `POST /api/v1/users/`
  - Request body:
    ```json
    {
      "email": "user@example.com",
      "phone": "+998901234567",
      "full_name": "Eshmatov Toshmat",
      "password": "user123",
      "role": "employee",
      "base_salary": 5000000,
      "expected_monthly_hours": 160
    }
    ```
- **Barcha xodimlarni ko‘rish**: `GET /api/v1/users/`

---

## 🛠 Admin yaratish
Agar yangi admin yaratish kerak bo‘lsa, host tizimda quyidagi buyruqni bering:
```bash
docker exec -i staffflow_app python3 < create_admin.py
```

---

## 🛡 Xavfsizlik va Tuzatishlar
- **Circular Import**: `UserRole` va `User` o'rtasidagi aylanma bog'liqlik hal qilindi.
- **Python 3.12 Compatibility**: `passlib`dagi xatolik sababli to'g'ridan-to'g'ri `bcrypt` kutubxonasiga o'tildi.
- **Rate Limiting**: Redis yordamida 5 marta xato login urinishidan so'ng 15 minutlik bloklash o'rnatilgan.
