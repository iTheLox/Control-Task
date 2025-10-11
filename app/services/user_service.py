from app.database import execute_query
from app.models import UserCreate, UserDB
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funciones de Seguridad ---

def get_password_hash(password: str) -> str:
    """
    Propósito: Generar el hash (cifrado) de una contraseña usando bcrypt.
    Parámetros de entrada:
        - password (str): La contraseña en texto plano.
    Qué retorna: La contraseña cifrada (str).
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Propósito: Verificar si una contraseña en texto plano coincide con su hash almacenado.
    Parámetros de entrada:
        - plain_password (str): Contraseña ingresada por el usuario.
        - hashed_password (str): Hash de la contraseña almacenada en la DB.
    Qué retorna: True si coinciden, False en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)

# --- Funciones CRUD de Usuario ---

def get_user_by_username(username: str):
    """
    Propósito: Buscar un usuario por su nombre de usuario en la base de datos.
    Parámetros de entrada:
        - username (str): Nombre de usuario a buscar.
    Qué retorna: Un diccionario con los datos del usuario si lo encuentra, o None.
    """
    query = "SELECT id, username, email, hashed_password FROM users WHERE username = %s"
    user_data = execute_query(query, (username,), fetch_one=True)
    return user_data

def get_user_by_email(email: str):
    """
    Propósito: Buscar un usuario por su dirección de correo electrónico en la base de datos.
    Parámetros de entrada:
        - email (str): Email a buscar.
    Qué retorna: Un diccionario con los datos del usuario si lo encuentra, o None.
    """
    query = "SELECT id, username, email, hashed_password FROM users WHERE email = %s"
    user_data = execute_query(query, (email,), fetch_one=True)
    return user_data

def create_user(user: UserCreate):
    """
    Propósito: Insertar un nuevo usuario en la base de datos con su contraseña hasheada.
    Parámetros de entrada:
        - user (UserCreate): Modelo Pydantic con username, email y password.
    Qué retorna: El ID del nuevo usuario si se insertó con éxito, o None.
    """
    if get_user_by_username(user.username) or get_user_by_email(user.email):
        logger.warning(f"Intento de registro fallido: Usuario o email ya existen.")
        return None # Usuario o email ya existen

    hashed_password = get_password_hash(user.password)
    
    query = "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)"
    params = (user.username, user.email, hashed_password)
    
    # execute_query retorna el lastrowid para un INSERT exitoso
    new_user_id = execute_query(query, params) 
    
    if new_user_id:
        logger.info(f"Usuario {user.username} registrado con éxito con ID: {new_user_id}")
    else:
        logger.error(f"Fallo al registrar el usuario {user.username} en la base de datos.")
        
    return new_user_id
