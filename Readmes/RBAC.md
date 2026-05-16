# 🔐 StaffFlow RBAC (Role-Based Access Control) Sistemi

Ushbu modul tizimdagi foydalanuvchilarning ruxsatlarini granular (aniq) boshqarish uchun mo'ljallangan. Tizim **SOLID** tamoyillari asosida qurilgan bo'lib, dinamik rollar va ruxsatnomalar (permissions) yaratish imkonini beradi.

## 🚀 Imkoniyatlar

- **Dinamik Rollar:** Ma'mur (Admin) xohlagancha yangi rollar (masalan: `Accountant`, `Team Lead`) yaratishi mumkin.
- **Aniq Ruxsatnomalar:** Har bir amal uchun alohida ruxsatnoma (masalan: `report:export`, `user:edit`) yaratish va ularni rollarga biriktirish.
- **Foydalanuvchi-Rol Bog'liqligi:** Bir foydalanuvchiga bir nechta rollarni biriktirish imkoniyati.
- **Moslashuvchanlik:** Mavjud tizim bilan to'liq mos keladi (eski `role` maydoni saqlangan holda bosqichma-bosqich yangi tizimga o'tish mumkin).

## 📂 Modul Tuzilishi

```text
app/modules/rbac/
├── models.py          # Role, Permission va bog'lanish jadvallari
├── schemas.py         # Pydantic modellar (Validatsiya)
├── service.py         # CRUD va biznes mantiqi
├── endpoints.py       # API endpointlar
└── dependencies.py    # require_permission dekoratori
```

## 🛠 Ishlatish bo'yicha qo'llanma

### 1. Ruxsatnoma (Permission) yaratish
Dastlab, tizimdagi amallar uchun ruxsatnomalar yaratiladi:
`POST /api/v1/rbac/permissions`
```json
{
  "name": "report:export",
  "description": "Hisobotlarni eksport qilish ruxsati"
}
```

### 2. Rol yaratish va ruxsatnomalarni biriktirish
`POST /api/v1/rbac/roles`
```json
{
  "name": "HR_Premium",
  "description": "Kengaytirilgan ruxsatlarga ega HR"
}
```
So'ngra ruxsatnomalarni rolga biriktiring:
`POST /api/v1/rbac/roles/{role_id}/permissions`

### 3. Foydalanish bo'yicha API Endpointlar

Barcha RBAC endpointlari faqat **Admin** foydalanuvchisi uchun ochiq.

| Metod | Endpoint | Tavsif |
| :--- | :--- | :--- |
| `GET` | `/api/v1/rbac/permissions` | Barcha ruxsatnomalar ro'yxati |
| `POST` | `/api/v1/rbac/permissions` | Yangi ruxsatnoma yaratish |
| `GET` | `/api/v1/rbac/roles` | Barcha rollar va ularning ruxsatlari |
| `POST` | `/api/v1/rbac/roles` | Yangi rol yaratish |
| `POST` | `/api/v1/rbac/roles/{id}/permissions` | Rolga ruxsatlar biriktirish |
| `POST` | `/api/v1/rbac/users/{id}/roles` | Foydalanuvchiga rollar biriktirish |

#### 💡 Misollar:

**Rolga ruxsatlar biriktirish:**
`POST /api/v1/rbac/roles/2/permissions`
```json
{
  "permission_ids": [1, 2, 5]
}
```

**Foydalanuvchiga rollar biriktirish:**
`POST /api/v1/rbac/users/10/roles`
```json
{
  "role_ids": [1, 3]
}
```

### 4. API endpointni himoyalash
Kod ichida istalgan endpointni quyidagicha himoya qiling:

```python
from app.modules.rbac.dependencies import require_permission

@router.get("/secret-data", dependencies=[Depends(require_permission("report:export"))])
async def get_data():
    return {"data": "Maxfiy hisobot"}
```

## 🛡 Xavfsizlik

- Faqat `UserRole.ADMIN` (tizim asosi) RBAC sozlamalarini o'zgartira oladi.
- Admin foydalanuvchilari barcha ruxsatnomalarga avtomatik ega hisoblanadi (`*` permission).
- Barcha amallar asinxron (async/await) bajariladi, bu esa yuqori unumdorlikni ta'minlaydi.

---
*StaffFlow - Ish jarayonlarini aqlli boshqarish tizimi.*
