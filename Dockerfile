# Usa una imagen base ligera
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
COPY requirements.txt .
# --no-cache-dir para mantener la imagen liviana
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY app/ app/

# Expone el puerto por defecto de Uvicorn (FastAPI)
EXPOSE 8000

# Comando para correr la aplicación con Uvicorn.
# Nota: El comando principal ya se definió en docker-compose.yml para incluir un 'sleep'.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
