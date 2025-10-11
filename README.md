# Control-Task — Backend FastAPI + MySQL (resumen rápido)

Proyecto de ejemplo: backend en FastAPI con persistencia en MySQL y frontend estático (HTML/JS).

Archivos clave
- `app/main.py` — Entrypoint de FastAPI y endpoints principales.
- `app/auth.py` — JWT: creación y verificación de tokens.
- `app/database.py` — Conexión a MySQL y helpers (`execute_query`, `create_initial_tables`).
- `app/services/` — Lógica de negocio: `user_service.py`, `task_service.py`.
- `Dockerfile`, `docker-compose.yml` — configuración para levantar DB y backend.

Arrancar localmente (sin Docker)
1. Crear entorno virtual e instalar dependencias:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Crear `.env` en la raíz (ejemplo en `.env.example`) y ajustar `MYSQL_HOST` a `127.0.0.1` si usas MySQL local.
3. Ejecutar la app:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

Arrancar con Docker (recomendado)
1. Copiar `.env.example` a `.env` y rellenar valores reales (no commitear `.env`).
2. Ejecutar:
   ```powershell
   docker-compose up --build
   ```
3. Comprobar `http://localhost:8000/docs`.

Cambios recientes aplicados
- `app/database.py`: default `MYSQL_HOST` ahora es `db` para compatibilidad Docker.
- `.dockerignore` añadido.
- `.env.example` añadido.
- `.github/copilot-instructions.md` añadido con guías para agentes.
- `app/services/user_service.py`: `create_user` ahora retorna booleano (True/False) y existe `create_user_record` para uso directo con valores ya hasheados.

Notas finales
- Si quieres que unifique routers (mover endpoints a `app/routes/` y usar `app.include_router()`), puedo hacerlo; es un refactor seguro pero requiere pruebas.
