# ── Imagen base: Python 3.8 (requerido por el enunciado) ──────────────────────
FROM python:3.8-slim
 
# Variables de entorno para evitar archivos .pyc y logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
 
# Directorio de trabajo dentro del contenedor
WORKDIR /app
 
# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
# Copiar e instalar dependencias de Python primero (capa cacheada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copiar el código fuente
COPY . .
 
# Exponer el puerto en el que corre la app
EXPOSE 5000
 
# Gunicorn como servidor WSGI de producción
# Flask 1.1.x es compatible con Gunicorn 20.x
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "120", "app:app"]
 