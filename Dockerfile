# Usa una imagen base ligera
FROM python:3.11-slim

# Instala utilidades necesarias (como curl para el healthcheck)
RUN apt-get update && apt-get install -y curl && apt-get clean

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requisitos e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY app/ app/

# Expone el puerto por defecto de Uvicorn (FastAPI)
EXPOSE 8000

# Comando para correr la aplicación con Uvicorn
# Nota: el docker-compose puede sobrescribir este CMD si se requiere un delay para MySQL/Redis
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
