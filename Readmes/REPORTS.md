# Reports & Analytics Module API

Ushbu modul Admin va HR menejerlari uchun kompaniya ko'rsatkichlarini tahlil qilish va hisobotlarni yuklab olish imkonini beradi.

## Endpointlar

### 1. Dashboard Summary
Asosiy metrikalar (Xodimlar soni, bugun kelganlar, kechikkanlar va oylik payroll).
- **URL:** `/api/v1/reports/dashboard-summary`
- **Metod:** `GET`
- **Ruxsat:** `HR_MANAGER`, `ADMIN`

### 2. Davomat hisoboti
Ma'lum vaqt oralig'ida barcha xodimlar uchun umumiy davomat statistikasi (ish soatlari, kechikishlar).
- **URL:** `/api/v1/reports/attendance`
- **Metod:** `GET`
- **Parametrlar:** `start_date`, `end_date` (Format: YYYY-MM-DD)

### 3. Maosh hisoboti
Ma'lum bir oy uchun barcha xodimlarning hisoblangan maoshlari.
- **URL:** `/api/v1/reports/salary`
- **Metod:** `GET`
- **Parametrlar:** `month`, `year`

### 4. Eksport (Excel/CSV)
Hisobotlarni CSV formatida yuklab olish.
- **URL:** `/api/v1/reports/export/attendance/csv`
- **Metod:** `GET`
- **Parametrlar:** `start_date`, `end_date`
- **Javob:** `attendance_report.csv` fayli.

## Xavfsizlik
Barcha endpointlar faqat `HR_MANAGER` va `ADMIN` rollari uchun ochiq. Oddiy xodimlar (`EMPLOYEE`) ushbu ma'lumotlarni ko'ra olmaydi.
