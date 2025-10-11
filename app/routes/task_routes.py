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
    new_id = create_new_task(task, current_user["id"])
    if not new_id:
        raise HTTPException(status_code=500, detail="Error al crear tarea.")
    task_data = get_task_by_id(new_id, current_user["id"])
    return task_data


@router.get("/", response_model=List[TaskDB])
async def list_tasks(current_user=Depends(get_current_user)):
    return get_user_tasks(current_user["id"])


@router.patch("/{task_id}")
async def edit_task(task_id: int, task: TaskUpdate, current_user=Depends(get_current_user)):
    updated = update_task(task_id, current_user["id"], task)
    if not updated:
        raise HTTPException(status_code=404, detail="Tarea no encontrada o no pertenece al usuario.")
    return {"message": "Tarea actualizada correctamente."}


@router.delete("/{task_id}")
async def remove_task(task_id: int, current_user=Depends(get_current_user)):
    deleted = delete_task(task_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Tarea no encontrada o no pertenece al usuario.")
    return {"message": "Tarea eliminada correctamente."}
