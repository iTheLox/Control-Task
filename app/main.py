import os
import logging
import redis # Usado para la conexión al broker/cache.
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
# Importaciones desde módulos locales:
from app.database import get_db_connection, create_initial_tables # Funciones de conexión de MySQL.
from app.models import UserCreate, UserDB, TaskCreate, TaskUpdate, TaskDB, Token # Modelos de datos (Pydantic).
from app.services import user_service, task_service # Lógica de negocio para usuarios y tareas.
from app.auth import get_current_user, create_access_token # Lógica de autenticación (JWT).
from app.routes import upload as upload_router # Router para manejar la carga de archivos.

# ---------------------------------------------------------
# ⚙️ CONFIGURACIÓN BASE DE LA APLICACIÓN
# ---------------------------------------------------------
# Creación de la instancia principal de FastAPI.
app = FastAPI(
    title="Task Manager API",
    description="Backend de gestión de tareas con FastAPI, MySQL y Celery",
    version="1.0.0"
)

# 🌐 Configuración de CORS (Cross-Origin Resource Sharing)
# Define qué orígenes (dominios) pueden hacer peticiones a esta API.
origins = [
    "http://localhost:5500",  # Origen común para Live Server (VS Code).
    "http://127.0.0.1:5500",
    "null"                    # Necesario si se abre el HTML directamente desde el disco.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Permite las URLs definidas arriba.
    allow_credentials=True,      # Permite cookies de autenticación, encabezados de autorización, etc.
    allow_methods=["*"],         # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.).
    allow_headers=["*"],         # Permite todos los encabezados HTTP.
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
    Función que se ejecuta inmediatamente después de que Uvicorn/FastAPI comienza a cargar.
    Asegura que la base de datos esté lista antes de aceptar peticiones.
    """
    logger.info("🔄 Iniciando aplicación... Verificando conexión a MySQL...")
    # Llama a la función del gestor de DB para crear las tablas si no existen.
    if not create_initial_tables():
        logger.error("❌ Error al crear/verificar tablas en MySQL. Revisa tu conexión.")
    logger.info("✅ Verificación de tablas completada con éxito.")


# ---------------------------------------------------------
# 🧠 ENDPOINT DE SALUD (HEALTH CHECK)
# ---------------------------------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Endpoint de salud que verifica el estado de los componentes vitales (DB y Redis).
    
    NOTA IMPORTANTE: El healthcheck de Docker (en docker-compose.yml) solo usa la primera línea
    (return {"status": "ok"}) para una respuesta rápida. El resto del código realiza una
    verificación profunda para fines de monitoreo de la aplicación.
    """
    
    # Respuesta rápida para Docker 
    # return {"status": "ok"} 
    
    # --- Verificación de MySQL ---
    conn = get_db_connection()
    db_ok = False
    if conn:
        try:
            # Intenta hacer un ping a la conexión activa para verificar que sigue viva.
            conn.ping(reconnect=True, attempts=3, delay=1)
            db_ok = True
        except:
            db_ok = False
        finally:
            # Asegura que la conexión se cierre.
            try:
                conn.close()
            except:
                pass

    # --- Verificación de Redis ---
    redis_ok = False
    try:
        # Intenta conectarse a Redis usando la URL de entorno (que en Docker es 'redis:6379').
        REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
        r = redis.from_url(REDIS_URL)
        # Ejecuta el comando PING para verificar conectividad.
        if r.ping():
            redis_ok = True
    except:
        redis_ok = False

    # Devuelve el estado combinado.
    status_text = "healthy" if db_ok and redis_ok else "unhealthy"
    return {"status": status_text, "db": db_ok, "redis": redis_ok}


# ---------------------------------------------------------
# 👤 REGISTRO Y LOGIN DE USUARIOS
# ---------------------------------------------------------
@app.post("/register", response_model=UserDB, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    """
    Endpoint para registrar un nuevo usuario.
    """
    # Verifica si el usuario o email ya existen.
    if user_service.get_user_by_username(user.username) or user_service.get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="El nombre de usuario o email ya están en uso.")

    # Crea el usuario en la DB (hashing de contraseña ocurre dentro del servicio).
    created = user_service.create_user(user)
    if not created:
        raise HTTPException(status_code=500, detail="Error al crear el usuario en la base de datos.")

    # Retorna los datos del usuario (sin la contraseña hasheada).
    new_user_data = user_service.get_user_by_username(user.username)
    return UserDB(**{k: v for k, v in new_user_data.items() if k != 'hashed_password'})


@app.post("/token", response_model=Token)
# OAuth2PasswordRequestForm es una dependencia de FastAPI para manejar el login de forma estándar.
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint para el login. Verifica credenciales y genera un token JWT.
    """
    user_data = user_service.get_user_by_username(form_data.username)
    # Verifica si el usuario existe y si la contraseña es correcta.
    if not user_data or not user_service.verify_password(form_data.password, user_data.get('hashed_password')):
        # Si falla, lanza 401 Unauthorized con el encabezado requerido para OAuth2.
        raise HTTPException(
            status_code=401,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Genera el token JWT.
    access_token = create_access_token(data={"sub": user_data['username']})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserDB)
# Depends(get_current_user) extrae el token JWT del encabezado y verifica la autenticidad.
def read_users_me(current_user: UserDB = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado a partir del token JWT.
    """
    return current_user


# ---------------------------------------------------------
# 🧩 CRUD DE TAREAS (Requiere Autenticación)
# ---------------------------------------------------------
@app.post("/tasks", response_model=TaskDB, status_code=status.HTTP_201_CREATED)
def create_task_for_current_user(task: TaskCreate, current_user: UserDB = Depends(get_current_user)):
    """
    Crea una nueva tarea, asociándola al ID del usuario autenticado.
    """
    new_id = task_service.create_new_task(task, current_user.id)
    if new_id is None:
        raise HTTPException(status_code=500, detail="Error al crear la tarea.")
        
    created_task_data = task_service.get_task_by_id(new_id, current_user.id)
    return TaskDB(**created_task_data)


@app.get("/tasks", response_model=list[TaskDB])
def read_tasks(current_user: UserDB = Depends(get_current_user)):
    """
    Lista todas las tareas que pertenecen al usuario autenticado.
    """
    tasks_data = task_service.get_user_tasks(current_user.id)
    # Convierte la lista de diccionarios de la DB a la lista de modelos Pydantic (TaskDB).
    return [TaskDB(**task) for task in tasks_data]


@app.patch("/tasks/{task_id}", response_model=TaskDB)
def update_task(task_id: int, task: TaskUpdate, current_user: UserDB = Depends(get_current_user)):
    """
    Actualiza una tarea existente. Primero verifica que la tarea exista y pertenezca al usuario.
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
    Elimina una tarea existente. Primero verifica que la tarea exista y pertenezca al usuario.
    """
    if not task_service.get_task_by_id(task_id, current_user.id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada o no te pertenece.")
        
    if not task_service.delete_task(task_id, current_user.id):
        raise HTTPException(status_code=500, detail="Error al eliminar la tarea.")
        
    return None # HTTP 204 NO_CONTENT no retorna cuerpo.

# Importa una respuesta de archivo para servir una página HTML.
from fastapi.responses import FileResponse 

@app.get("/")
def index():
    """
    Endpoint de inicio que probablemente sirve un frontend HTML estático.
    """
    return FileResponse("app/static/upload.html")

# ---------------------------------------------------------
# 📦 RUTAS DEL CARGADOR MASIVO (EXCEL)
# ---------------------------------------------------------
# include_router: Monta las rutas definidas en el módulo 'upload' bajo el prefijo '/api'.
app.include_router(upload_router.router, prefix="/api", tags=["Cargador XLS"])

# ---------------------------------------------------------
# 🏁 EJECUCIÓN DEL SERVIDOR
# ---------------------------------------------------------
# (Estos comentarios son solo informativos, no se ejecutan como código)
# Se ejecuta desde consola con:
# uvicorn app.main:app --reload
# y en otra terminal: # celery -A app.celery_worker.celery worker --loglevel=info