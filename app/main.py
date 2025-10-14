import os
import logging
import redis
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db_connection, create_initial_tables
from app.models import UserCreate, UserDB, TaskCreate, TaskUpdate, TaskDB, Token
from app.services import user_service, task_service
from app.auth import get_current_user, create_access_token
from app.routes import upload as upload_router

# ---------------------------------------------------------
# ⚙️ CONFIGURACIÓN BASE DE LA APLICACIÓN
# ---------------------------------------------------------
app = FastAPI(
    title="Task Manager API",
    description="Backend de gestión de tareas con FastAPI, MySQL y Celery",
    version="1.0.0"
)

# 🌐 Configuración de CORS
origins = [
    "http://localhost:5500",  # Live Server
    "http://127.0.0.1:5500",
    "null"                    # Si abres el HTML directamente desde archivos
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📝 Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 🚀 EVENTOS DE INICIO
# ---------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """
    Evento que se ejecuta al iniciar la aplicación.
    Verifica la conexión y crea las tablas necesarias en MySQL.
    """
    logger.info("🔄 Iniciando aplicación... Verificando conexión a MySQL...")
    if not create_initial_tables():
        logger.error("❌ Error al crear/verificar tablas en MySQL. Revisa tu conexión.")
    logger.info("✅ Verificación de tablas completada con éxito.")


# ---------------------------------------------------------
# 🧠 ENDPOINT DE SALUD (HEALTH CHECK)
# ---------------------------------------------------------
@app.get("/health")
def health_check():
    """
    Verifica el estado de la conexión a MySQL y Redis.
    """
    # MySQL
    conn = get_db_connection()
    db_ok = False
    if conn:
        try:
            conn.ping(reconnect=True, attempts=3, delay=1)
            db_ok = True
        except:
            db_ok = False
        finally:
            try:
                conn.close()
            except:
                pass

    # Redis
    redis_ok = False
    try:
        REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(REDIS_URL)
        if r.ping():
            redis_ok = True
    except:
        redis_ok = False

    status_text = "healthy" if db_ok and redis_ok else "unhealthy"
    return {"status": status_text, "db": db_ok, "redis": redis_ok}


# ---------------------------------------------------------
# 👤 REGISTRO Y LOGIN DE USUARIOS
# ---------------------------------------------------------
@app.post("/register", response_model=UserDB, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    """
    Registrar un nuevo usuario.
    """
    if user_service.get_user_by_username(user.username) or user_service.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="El nombre de usuario o email ya están en uso.")

    created = user_service.create_user(user)
    if not created:
        raise HTTPException(status_code=500, detail="Error al crear el usuario en la base de datos.")

    new_user_data = user_service.get_user_by_username(user.username)
    return UserDB(**{k: v for k, v in new_user_data.items() if k != 'hashed_password'})


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login del usuario y generación de token JWT.
    """
    user_data = user_service.get_user_by_username(form_data.username)
    if not user_data or not user_service.verify_password(form_data.password, user_data.get('hashed_password')):
        raise HTTPException(
            status_code=401,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": user_data['username']})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserDB)
def read_users_me(current_user: UserDB = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado.
    """
    return current_user


# ---------------------------------------------------------
# 🧩 CRUD DE TAREAS
# ---------------------------------------------------------
@app.post("/tasks", response_model=TaskDB, status_code=status.HTTP_201_CREATED)
def create_task_for_current_user(task: TaskCreate, current_user: UserDB = Depends(get_current_user)):
    """
    Crear una nueva tarea para el usuario autenticado.
    """
    new_id = task_service.create_new_task(task, current_user.id)
    if new_id is None:
        raise HTTPException(status_code=500, detail="Error al crear la tarea.")
    created_task_data = task_service.get_task_by_id(new_id, current_user.id)
    return TaskDB(**created_task_data)


@app.get("/tasks", response_model=list[TaskDB])
def read_tasks(current_user: UserDB = Depends(get_current_user)):
    """
    Listar tareas del usuario autenticado.
    """
    tasks_data = task_service.get_user_tasks(current_user.id)
    return [TaskDB(**task) for task in tasks_data]


@app.patch("/tasks/{task_id}", response_model=TaskDB)
def update_task(task_id: int, task: TaskUpdate, current_user: UserDB = Depends(get_current_user)):
    """
    Actualizar una tarea existente.
    """
    if not task_service.get_task_by_id(task_id, current_user.id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada o no te pertenece.")
    if not task_service.update_task(task_id, current_user.id, task):
        raise HTTPException(status_code=500, detail="Error al actualizar la tarea.")
    updated_task_data = task_service.get_task_by_id(task_id, current_user.id)
    return TaskDB(**updated_task_data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, current_user: UserDB = Depends(get_current_user)):
    """
    Eliminar una tarea.
    """
    if not task_service.get_task_by_id(task_id, current_user.id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada o no te pertenece.")
    if not task_service.delete_task(task_id, current_user.id):
        raise HTTPException(status_code=500, detail="Error al eliminar la tarea.")
    return None

from fastapi.responses import FileResponse

@app.get("/")
def index():
    return FileResponse("app/static/upload.html")

# ---------------------------------------------------------
# 📦 RUTAS DEL CARGADOR MASIVO (EXCEL)
# ---------------------------------------------------------
app.include_router(upload_router.router, prefix="/api", tags=["Cargador XLS"])

# ---------------------------------------------------------
# 🏁 EJECUCIÓN DEL SERVIDOR
# ---------------------------------------------------------
# Se ejecuta desde consola con:
# uvicorn app.main:app --reload
# y en otra terminal:
# celery -A app.celery_worker.celery worker --loglevel=info
