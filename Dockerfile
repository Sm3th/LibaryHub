# Temel imaj
FROM python:3.9-slim

# PostgreSQL geliştirme araçlarını yükle
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev

# Çalışma dizinini ayarla
WORKDIR /app

# Gerekli dosyaları kopyala
COPY requirements.txt requirements.txt

# Gereklilikleri yükle
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Uygulamayı çalıştır
CMD ["flask", "run", "--host=0.0.0.0"]
