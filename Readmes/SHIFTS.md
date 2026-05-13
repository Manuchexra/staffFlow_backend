# Shift Management Module API

Ish smenalarini yaratish va xodimlarni jadvallarga biriktirish.

## Endpointlar

### 1. Smena turi yaratish (HR)
- **URL:** `/api/v1/shifts/`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "name": "Morning Shift",
    "start_time": "08:00:00",
    "end_time": "16:00:00",
    "description": "Standard morning hours"
  }
  ```

### 2. Xodimni smenaga biriktirish
- **URL:** `/api/v1/shifts/assign`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "user_id": 1,
    "shift_id": 2,
    "date": "2026-05-15"
  }
  ```
- **Eslatma:** Bir vaqtga to'g'ri keladigan (overlap) smenalar bloklanadi.

### 3. Smenalar jadvali
- **URL:** `/api/v1/shifts/assignments`
- **Metod:** `GET`
- **Parametr:** `target_date` (ixtiyoriy)

### 4. Xodimning smenalar tarixi
- **URL:** `/api/v1/shifts/history/{user_id}`
- **Metod:** `GET`
- **Ruxsat:** `HR_MANAGER`, `ADMIN`
