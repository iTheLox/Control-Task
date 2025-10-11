from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from app.services.user_service import get_user_by_username, get_user_by_email, create_user

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
    if get_user_by_username(username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya está en uso.")
    
    if get_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo electrónico ya está registrado.")

    hashed_password = pwd_context.hash(password)
    success = create_user(username=username, email=email, hashed_password=hashed_password)

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo registrar el usuario.")

    return {"message": "Usuario registrado con éxito."}
