# Gunakan image Python ringan
FROM python:3.9-slim

# Install FFmpeg (Wajib untuk konversi kodek & embed metadata)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Setup kerja direktori
WORKDIR /app

# Install library python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy kode aplikasi
COPY . .

# Jalankan aplikasi
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]