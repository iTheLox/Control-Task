from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import logging
from dotenv import load_dotenv
from app.services.user_service import get_user_by_username
from app.models import TokenData, UserDB

# Cargar variables de entorno (para prueba local)
load_dotenv()

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)

# Esquema de seguridad para FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Propósito: Crear un token JWT con la carga útil proporcionada.
    Parámetros de entrada:
        - data (dict): Carga útil a incluir en el token (ej. {"sub": username}).
        - expires_delta (timedelta): Tiempo de expiración opcional.
    Qué retorna: El token JWT codificado (str).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Propósito: Decodificar y validar un token JWT.
    Parámetros de entrada:
        - token (str): El token JWT a decodificar.
    Qué retorna: Un objeto TokenData (payload) si es válido, o None si hay un error.
    """
    try:
        # Decodifica el token, verifica la firma y la expiración
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            logger.warning("Token no contiene el campo 'sub' (username).")
            return None
        
        token_data = TokenData(username=username)
        return token_data
        
    except JWTError:
        # Error de firma, token expirado, o formato incorrecto
        logger.error("Error de decodificación o validación de JWT.")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Propósito: Dependencia de FastAPI para obtener el usuario autenticado a partir del token.
    Parámetros de entrada:
        - token (str): El token JWT inyectado automáticamente por OAuth2PasswordBearer.
    Qué retorna: Un objeto UserDB con los datos del usuario. Lanza HTTPException si falla.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception

    # Buscar el usuario en la DB para asegurarse de que exista
    user_data = get_user_by_username(token_data.username)
    if user_data is None:
        raise credentials_exception
    
    # Crear el modelo Pydantic del usuario
    # Excluimos la contraseña hasheada para que no se devuelva.
    user_model = UserDB(**{k: v for k, v in user_data.items() if k != 'hashed_password'})
    
    return user_model
