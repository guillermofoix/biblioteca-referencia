# Imagen base: Linux mínimo con Python 3.12 ya instalado.
FROM python:3.15-slim

# PYTHONDONTWRITEBYTECODE=1: Python no crea ficheros .pyc (no hacen falta en un contenedor).
# PYTHONUNBUFFERED=1: los print y logs salen al momento, así se ven en "docker compose logs".
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Carpeta de trabajo dentro del contenedor; los comandos siguientes se ejecutan aquí.
WORKDIR /app

# Se copia solo requirements.txt ANTES que el código: Docker guarda cada paso en caché
# y, si las dependencias no cambian, no las reinstala al modificar app.py.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ahora sí, el resto del código. Lo que no debe entrar (.env, .git...) lo filtra el .dockerignore.
COPY . .

# Usuario sin privilegios: si alguien explotara un fallo de la app, no sería root dentro del contenedor.
RUN useradd --no-create-home biblio
USER biblio

# Documenta que la app escucha en el puerto 5000 (no lo publica; eso lo hace docker-compose).
EXPOSE 5000

# Arranca la app con gunicorn (servidor de producción).
# 0.0.0.0 = escuchar en todas las interfaces; con 127.0.0.1 no se podría acceder desde fuera del contenedor.
# app:app = fichero app.py (módulo "app") y variable "app" (la aplicación Flask) dentro de él.
# --access-logfile -: así cada petición (GET / 200) aparece en "docker compose logs".
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]
