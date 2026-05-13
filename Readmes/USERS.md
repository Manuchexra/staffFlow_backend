# Users Module API

Xodimlarni boshqarish, profillarni tahrirlash va qidiruv tizimi.

## Endpointlar

### 1. Xodim yaratish (Admin/HR)
- **URL:** `/api/v1/users/`
- **Metod:** `POST`
- **Ruxsat:** `ADMIN`, `HR_MANAGER`
- **Body:** `UserCreate` sxemasi.

### 2. Xodimlarni qidirish va filtrlash
- **URL:** `/api/v1/users/`
- **Metod:** `GET`
- **Parametrlar:** 
  - `search`: Ism, telefon yoki email bo'yicha qidiruv.
  - `role`: Rol bo'yicha filtr (admin, hr_manager, employee).
  - `is_active`: Holati bo'yicha filtr (true/false).
- **Ruxsat:** `HR_MANAGER`, `ADMIN`

### 3. Xodim profilini ko'rish
- **URL:** `/api/v1/users/{user_id}`
- **Metod:** `GET`
- **Ruxsat:** `HR_MANAGER`, `ADMIN`

### 4. Xodim ma'lumotlarini tahrirlash
- **URL:** `/api/v1/users/{user_id}`
- **Metod:** `PATCH`
- **Body:** `UserUpdateHR` (rol, maosh, status va h.k.)
- **Ruxsat:** `HR_MANAGER`, `ADMIN`

### 5. O'z profilini tahrirlash
- **URL:** `/api/v1/users/me`
- **Metod:** `PUT`
- **Body:** `UserUpdateMe` (faqat shaxsiy ma'lumotlar)

### 6. Parolni qayta o'rnatish (HR tomonidan)
- **URL:** `/api/v1/users/{user_id}/reset-password`
- **Metod:** `POST`
- **Body:** `{"new_password": "string"}`

### 7. Rasmni yangilash
- **URL:** `/api/v1/users/me/avatar` (O'zi uchun)
- **URL:** `/api/v1/users/{user_id}/avatar` (HR tomonidan)
- **Metod:** `POST` (Multipart/form-data)
