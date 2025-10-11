from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from app.services.user_service import get_user_by_username, get_user_by_email, create_user_record, create_user

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterResponse(BaseModel):
    message: str

@router.post("/register", response_model=RegisterResponse)
def register_user(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    """
    Propósito: Registrar un usuario desde un formulario (x-www-form-urlencoded).
    Parámetros:
        - username, email, password (Form data).
    Retorna:
        - RegisterResponse con mensaje de éxito.
    Errores:
        - 400 si username/email ya existen.
        - 500 en errores inesperados.
    """
    if get_user_by_username(username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya está en uso.")

    if get_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo electrónico ya está registrado.")

    try:
        hashed_password = pwd_context.hash(password)
        # Usar create_user_record que devuelve boolean
        success = create_user_record(username=username, email=email, hashed_password=hashed_password)

        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo registrar el usuario.")

        return {"message": "Usuario registrado con éxito."}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")
