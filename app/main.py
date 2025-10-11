from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_initial_tables
from app.models import UserCreate, UserDB, TaskCreate, TaskUpdate, TaskDB, Token
from app.services import user_service, task_service
from app.auth import get_current_user, create_access_token
import logging

# 🔧 Inicialización de FastAPI con metadatos
app = FastAPI(
    title="Task Manager API",
    description="Backend de gestión de tareas con FastAPI y MySQL",
    version="1.0.0"
)

# 🌐 Configuración de CORS para permitir solicitudes desde el frontend
origins = [
    "http://localhost:5500",  # Live Server
    "null"                    # Si abres el HTML directamente desde el sistema de archivos
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📝 Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚙️ Evento de inicio para verificar/crear tablas
@app.on_event("startup")
def on_startup():
    logger.info("Iniciando aplicación. Verificando tablas de MySQL...")
    if not create_initial_tables():
        logger.error("La aplicación no puede iniciarse debido a fallos de conexión o creación de tablas.")
    logger.info("Verificación de tablas completada.")

# 🔐 Endpoint de registro
@app.post("/register", response_model=UserDB, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    if user_service.get_user_by_username(user.username) or user_service.get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o email ya está en uso."
        )
    
    new_id = user_service.create_user(user)
    if new_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo al registrar el usuario en la base de datos."
        )

    new_user_data = user_service.get_user_by_username(user.username)
    return UserDB(**{k: v for k, v in new_user_data.items() if k != 'hashed_password'})

# 🔐 Endpoint de login
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = user_service.get_user_by_username(form_data.username)
    
    if not user_data or not user_service.verify_password(form_data.password, user_data.get('hashed_password')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user_data['username']})
    return {"access_token": access_token, "token_type": "bearer"}

# 👤 Endpoint para obtener el usuario autenticado
@app.get("/users/me", response_model=UserDB)
def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

# 📌 Crear tarea
@app.post("/tasks", response_model=TaskDB, status_code=status.HTTP_201_CREATED)
def create_task_for_current_user(task: TaskCreate, current_user: UserDB = Depends(get_current_user)):
    new_id = task_service.create_new_task(task, current_user.id)
    if new_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo al crear la tarea en la base de datos."
        )
    created_task_data = task_service.get_task_by_id(new_id, current_user.id)
    return TaskDB(**created_task_data)

# 📌 Leer tareas
@app.get("/tasks", response_model=list[TaskDB])
def read_tasks(current_user: UserDB = Depends(get_current_user)):
    tasks_data = task_service.get_user_tasks(current_user.id)
    return [TaskDB(**task) for task in tasks_data]

# 📌 Actualizar tarea
@app.patch("/tasks/{task_id}", response_model=TaskDB)
def update_task_endpoint(task_id: int, task: TaskUpdate, current_user: UserDB = Depends(get_current_user)):
    if not task_service.get_task_by_id(task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o no te pertenece.")
    
    if not task_service.update_task(task_id, current_user.id, task):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo al actualizar la tarea.")

    updated_task_data = task_service.get_task_by_id(task_id, current_user.id)
    return TaskDB(**updated_task_data)


# Compatibilidad: aceptar PUT además de PATCH para clientes que aún usan PUT
@app.put("/tasks/{task_id}", response_model=TaskDB)
def update_task_endpoint_put(task_id: int, task: TaskUpdate, current_user: UserDB = Depends(get_current_user)):
    # Delegar en la misma lógica que PATCH para mantener compatibilidad
    return update_task_endpoint(task_id, task, current_user)

# 📌 Eliminar tarea
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_endpoint(task_id: int, current_user: UserDB = Depends(get_current_user)):
    if not task_service.get_task_by_id(task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada o no te pertenece.")

    if not task_service.delete_task(task_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo al eliminar la tarea.")
