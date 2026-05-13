# Attendance Module API

Xodimlarning ishga kelish-ketish vaqtlarini va geolokatsiyasini qayd etish.

## Endpointlar

### 1. Ishga kelish (Check-in)
- **URL:** `/api/v1/attendance/check-in`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "latitude": 41.3111,
    "longitude": 69.2405
  }
  ```
- **Eslatma:** Geofence (radius) tekshiruvi amalga oshiriladi.

### 2. Ishdan ketish (Check-out)
- **URL:** `/api/v1/attendance/check-out`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "latitude": 41.3111,
    "longitude": 69.2405
  }
  ```

### 3. Shaxsiy davomat tarixi
- **URL:** `/api/v1/attendance/my-attendance`
- **Metod:** `GET`
- **Ruxsat:** Barcha tizim foydalanuvchilari.
