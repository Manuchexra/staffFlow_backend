FROM python:3.12-slim

WORKDIR /app

# Kerakli paketlar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Butun loyihani nusxalash
COPY . .

# Portni ochish
EXPOSE 8000

# Ishga tushirish buyrug‘i
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]