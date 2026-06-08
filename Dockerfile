# ---------- Etapa 1: compilar el dashboard (React/Vite) ----------
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---------- Etapa 2: backend FastAPI + Tesseract OCR ----------
FROM python:3.11-slim

# OCR local (Tesseract con español e inglés). No consume tokens de ninguna API.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
# Dashboard compilado servido por el mismo backend en "/"
COPY --from=frontend /fe/dist ./app/static

# Datos persistentes (BD SQLite + imágenes) en /data -> montar volumen en easypanel
ENV TESSERACT_CMD=tesseract \
    TESSERACT_LANG=spa+eng \
    MEDIA_DIR=/data/media \
    DATABASE_URL=sqlite:////data/app.db \
    PARSE_MODE=rules

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
