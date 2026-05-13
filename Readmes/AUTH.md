# Authentication Module API

Ushbu modul foydalanuvchilarni autentifikatsiya qilish, OTP orqali tasdiqlash va sessiyalarni boshqarish uchun xizmat qiladi.

## Endpointlar

### 1. Login (1-qadam)
Foydalanuvchi tizimga kirishi uchun birinchi qadam. Agar yangi qurilmadan kirilayotgan bo'lsa, OTP yuboriladi.
- **URL:** `/api/v1/auth/login`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "identifier": "phone_number_or_email",
    "password": "your_password"
  }
  ```
- **Javob:** `TokenResponse` (agar qurilma tanish bo'lsa) yoki `OTPResponse` (agar OTP kerak bo'lsa).

### 2. OTP Tasdiqlash (2-qadam)
Yangi qurilmadan kirilganda yuborilgan 6 raqamli kodni tasdiqlash.
- **URL:** `/api/v1/auth/verify-otp`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "temp_auth_token": "string",
    "otp": "123456"
  }
  ```

### 3. Tokenni Yangilash (Refresh Token)
Access token muddati tugaganda yangisini olish.
- **URL:** `/api/v1/auth/refresh`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "refresh_token": "your_refresh_token"
  }
  ```

### 4. Chiqish (Logout)
Sessiyani yakunlash va tokenni bekor qilish.
- **URL:** `/api/v1/auth/logout`
- **Metod:** `POST`
- **Auth:** Required (Bearer Token)
