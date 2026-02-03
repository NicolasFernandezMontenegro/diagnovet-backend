# Dockerfile
FROM python:3.10-slim

# Evita que Python genere archivos .pyc y buffer de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer el puerto (Cloud Run inyecta la variable PORT, por defecto 8080)
ENV PORT=8080

# Comando de ejecución
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]