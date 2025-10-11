from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Modelos de Usuarios ---

class UserBase(BaseModel):
    """
    Propósito: Define los campos comunes para crear o actualizar un usuario.
    """
    username: str
    email: str

class UserCreate(UserBase):
    """
    Propósito: Modelo para el registro (incluye la contraseña).
    """
    password: str

class UserDB(UserBase):
    """
    Propósito: Modelo de usuario tal como se recupera de la base de datos.
    """
    id: int

    class Config:
        # Permite que Pydantic maneje datos de la base de datos (ORM Mode)
        from_attributes = True

class Token(BaseModel):
    """
    Propósito: Modelo para el token JWT retornado tras el login.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Propósito: Modelo para los datos contenidos dentro del token JWT (payload).
    """
    username: Optional[str] = None

# --- Modelos de Tareas ---

class TaskBase(BaseModel):
    """
    Propósito: Define los campos comunes para crear o actualizar una tarea.
    """
    title: str
    description: Optional[str] = None
    completed: bool = False
    # Fechas opcionales (datetime). La BD retorna DATETIME que mapeará a datetime.
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskCreate(TaskBase):
    """
    Propósito: Modelo para la creación de una tarea.
    """
    pass

class TaskUpdate(TaskBase):
    """
    Propósito: Modelo para la actualización de una tarea (todos los campos opcionales).
    """
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    completed_at: Optional[datetime] = None

class TaskDB(TaskBase):
    """
    Propósito: Modelo de tarea tal como se recupera de la base de datos.
    """
    id: int
    owner_id: int

    class Config:
        from_attributes = True

