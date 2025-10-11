from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models import TaskCreate, TaskUpdate, TaskDB
from app.services.task_service import (
    create_new_task, get_user_tasks, get_task_by_id,
    update_task, delete_task
)
from app.auth import get_current_user  # asegúrate que esté en tu auth.py

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskDB)
async def create_task(task: TaskCreate, current_user=Depends(get_current_user)):
    """
    Propósito: Crear una nueva tarea para el usuario autenticado.
    Parámetros:
        - task (TaskCreate): datos de la tarea.
        - current_user: inyectado por get_current_user.
    Retorna:
        - TaskDB con la tarea creada.
    Errores:
        - 500 en caso de fallo en BD.
    """
    try:
        new_id = create_new_task(task, current_user["id"])
        if not new_id:
            raise HTTPException(status_code=500, detail="Error al crear tarea.")
        task_data = get_task_by_id(new_id, current_user["id"])
        return task_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/", response_model=List[TaskDB])
async def list_tasks(current_user=Depends(get_current_user)):
    """
    Propósito: Listar tareas del usuario autenticado.
    Retorna:
        - List[TaskDB]
    """
    try:
        return get_user_tasks(current_user["id"])
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.patch("/{task_id}")
async def edit_task(task_id: int, task: TaskUpdate, current_user=Depends(get_current_user)):
    """
    Propósito: Actualizar una tarea.
    Retorna:
        - Mensaje de éxito o 404 si no existe.
    """
    try:
        updated = update_task(task_id, current_user["id"], task)
        if not updated:
            raise HTTPException(status_code=404, detail="Tarea no encontrada o no pertenece al usuario.")
        return {"message": "Tarea actualizada correctamente."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/{task_id}")
async def remove_task(task_id: int, current_user=Depends(get_current_user)):
    """
    Propósito: Eliminar una tarea.
    Retorna:
        - Mensaje de éxito o 404 si no existe.
    """
    try:
        deleted = delete_task(task_id, current_user["id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Tarea no encontrada o no pertenece al usuario.")
        return {"message": "Tarea eliminada correctamente."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
