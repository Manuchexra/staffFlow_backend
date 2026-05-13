# Salary Module API

Oylik maoshlarni hisoblash, bonus, jarima va avanslarni boshqarish.

## Endpointlar

### 1. Maoshni ko'rish (Employee)
Xodim joriy yoki o'tgan oylar uchun o'z maoshi hisobotini ko'radi.
- **URL:** `/api/v1/salary/my`
- **Metod:** `GET`
- **Parametrlar:** `month`, `year`

### 2. Oylik hisoblash (Admin/HR)
Xodim uchun oylik ish soatlari va tranzaksiyalar asosida maoshni shakllantirish.
- **URL:** `/api/v1/salary/calculate/{user_id}`
- **Metod:** `POST`
- **Body:** `{"month": 5, "year": 2026}`

### 3. Tranzaksiya qo'shish (Bonus/Jarima/Avans)
- **URL:** `/api/v1/salary/transactions?user_id=1`
- **Metod:** `POST`
- **Body:**
  ```json
  {
    "type": "bonus", 
    "amount": 500000,
    "reason": "Yaxshi natija uchun"
  }
  ```
- **Turlari:** `bonus`, `penalty`, `advance`.

### 4. Maoshlar tarixi
- **URL:** `/api/v1/salary/my/history` - Shaxsiy tarix.
- **URL:** `/api/v1/salary/all` - Barcha xodimlar hisoboti (Admin/HR).
- **URL:** `/api/v1/salary/my/yearly-summary` - Yillik jamlama.
