# Notifications Module API

Ushbu modul real vaqtda (WebSocket) va in-app bildirishnomalarni boshqarish uchun xizmat qiladi.

## Endpointlar

### 1. Bildirishnomalar tarixini ko'rish
- **URL:** `/api/v1/notifications/`
- **Metod:** `GET`
- **Parametrlar:** `only_unread` (true/false)
- **Auth:** Required

### 2. O'qilgan deb belgilash
- **URL:** `/api/v1/notifications/read/{notif_id}` - Bitta xabar uchun.
- **URL:** `/api/v1/notifications/read-all` - Barcha xabarlar uchun.
- **Metod:** `POST`

### 3. Bildirishnoma yuborish (Admin/HR)
Xabarni individual xodimga, ma'lum bir rolga (masalan: barcha xodimlarga) yoki tizimdagi hamma foydalanuvchilarga yuborish.
- **URL:** `/api/v1/notifications/send`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "title": "E'lon",
    "message": "Ertaga dam olish kuni!",
    "type": "info",
    "role": "employee", 
    "to_all": false
  }
  ```

### 4. Push Token saqlash
Mobil yoki web push bildirishnomalar uchun tokenni bazaga saqlash.
- **URL:** `/api/v1/notifications/device-token`
- **Metod:** `POST`
- **Body:** `{"fcm_token": "string", "device_type": "web"}`

## Real-time (WebSocket)

Real vaqtda bildirishnomalarni qabul qilish uchun WebSocket ulanishidan foydalaning.

- **URL:** `ws://your-domain.com/api/v1/notifications/ws/{access_token}`
- **Ulanishda:** Foydalanuvchi `access_token` orqali autentifikatsiya qilinadi.
- **Xabar formati:** Tizim yangi bildirishnoma yuborganda WebSocket orqali JSON formatida xabar keladi:
  ```json
  {
    "type": "notification",
    "title": "Sizning maoshingiz hisoblandi",
    "message": "Batafsil maosh bo'limida ko'ring",
    "notif_type": "success"
  }
  ```
