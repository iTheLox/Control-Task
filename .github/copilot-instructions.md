# Instrucciones rápidas para agentes de codificación (Control-Task)

Contexto breve
- Backend: FastAPI (Python). Frontend: HTML/JS estático. DB: MySQL en contenedor.
- Código principal en `app/`. Entrypoint de la API: `app/main.py`.

Qué buscar primero
- `app/main.py` — configuración de FastAPI, CORS, endpoints principales (register, token, tasks).
- `app/auth.py` — JWT: `create_access_token`, `get_current_user` (depende de `SECRET_KEY`).
- `app/database.py` — `get_db_connection`, `execute_query`, `create_initial_tables` (lee variables desde `.env`).
- `app/services/` — lógica de negocio: `user_service.py`, `task_service.py`.
- `docker-compose.yml` — define servicios `db` (MySQL) y `backend` (construye Dockerfile) y usa `.env`.

Patrones y convenciones del proyecto
- DB: todo acceso pasa por `app.database.execute_query(sql, params, fetch_one, fetch_all)`.
  - SELECT usa `cursor(dictionary=True)` y devuelve dicts.
  - INSERT devuelve `lastrowid`.
- Seguridad: passwords con `passlib[bcrypt]`, tokens con `python-jose` (campo `sub` en payload).
- Rutas y servicios: la lógica de negocio está en `app/services/*` y `main.py` o `app/routes/*` exponen endpoints.
  - Nota: hay duplicidad parcial entre endpoints en `main.py` y `app/routes/` — prefiera mantener APIRouter en `routes/` y hacer `app.include_router()`.

Errores comunes al modificar/ejecutar
- Asegurar que `.env` contenga `MYSQL_HOST=db` cuando se usa Docker (el proyecto ahora asume `db` por defecto).
- Evitar hardcodear secretos: `SECRET_KEY` debe venir de `.env`.
- Consistencia en retornos: `create_user` puede devolver ID o boolean; validar uso al editar rutas.

Cómo arrancar localmente (desarrollo rápido)
1. Crear entorno virtual e instalar dependencias:
   python3 -m venv venv
   source venv/bin/activate    # en Windows PowerShell: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
2. Crear `.env` con al menos:
   SECRET_KEY=un_valor_secreto
   MYSQL_HOST=127.0.0.1
   MYSQL_USER=tu_usuario
   MYSQL_PASSWORD=tu_password
   MYSQL_DATABASE=taskdb
   BACKEND_PORT=8000
3. Ejecutar la app (sin Docker):
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Cómo arrancar con Docker (recomendado para presentaciones)
1. Crear `.env` en la raíz (no versionar) con variables:
   MYSQL_ROOT_PASSWORD=secretroot
   MYSQL_DATABASE=taskdb
   MYSQL_USER=taskuser
   MYSQL_PASSWORD=taskpass
   MYSQL_HOST=db
   BACKEND_PORT=8000
   SECRET_KEY=tu_secreto_aqui
2. Levantar los servicios:
   docker-compose up --build
3. Verificar: abrir `http://localhost:8000/docs` (Swagger). Abrir `tasks.html` o `index.html` localmente como frontend.

Arrancar este proyecto desde otra PC (guía breve)
1. Clonar el repo:
   git clone <repo-url>
   cd Control-Task
2. Copiar/crear `.env` en la raíz con las variables indicadas arriba. IMPORTANTE: no incluir credenciales reales en Git.
3. Si vas a usar Docker (recomendado): asegurarte de tener Docker y Docker Compose instalados. Ejecutar:
   docker-compose up --build
   - Esto levantará MySQL y el backend. El backend espera unos segundos antes de conectar.
4. Si no usas Docker (solo local): crear venv e instalar `requirements.txt`, ajustar `MYSQL_HOST` para apuntar a tu MySQL local.

Cambios aplicados por el agente
- `app/database.py`: ahora usa `MYSQL_HOST` con default `db` para compatibilidad con Docker.
- Se añadió `.dockerignore` para excluir `venv`, `.env` y archivos temporales.

Reglas rápidas para el agente
- No cambies esquemas de tablas sin migraciones (no hay sistema de migraciones aquí).
- Mantén la separación: los endpoints deben delegar en `services/*` para la lógica.
- Usa logs (logging) y maneja None/errores devueltos por `execute_query`.

Si algo está ambiguo o quieres que aplique cambios extra (tests, consolidar routers, o añadir un README de despliegue), dime y lo implemento.
