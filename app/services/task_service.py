from app.database import execute_query
from app.models import TaskCreate, TaskUpdate, TaskDB
import logging

logger = logging.getLogger(__name__)

# --- Funciones CRUD de Tareas ---

def create_new_task(task: TaskCreate, owner_id: int):
    """
    Propósito: Insertar una nueva tarea en la base de datos asociada a un usuario.
    Parámetros de entrada:
        - task (TaskCreate): Modelo Pydantic con title, description y completed.
        - owner_id (int): ID del usuario dueño de la tarea.
    Qué retorna: El ID de la nueva tarea si se insertó con éxito, o None.
    """
    # created_at lo maneja la BD con DEFAULT CURRENT_TIMESTAMP
    query = "INSERT INTO tasks (title, description, completed, owner_id) VALUES (%s, %s, %s, %s)"
    params = (task.title, task.description, task.completed, owner_id)

    # execute_query retorna el lastrowid para un INSERT
    new_task_id = execute_query(query, params)

    if new_task_id:
        logger.info(f"Tarea creada con éxito para el usuario {owner_id}, ID: {new_task_id}")
    else:
        logger.error(f"Fallo al crear la tarea para el usuario {owner_id}.")

    return new_task_id

def get_user_tasks(owner_id: int):
    """
    Propósito: Recuperar todas las tareas asociadas a un ID de usuario específico.
    Parámetros de entrada:
        - owner_id (int): ID del usuario cuyas tareas se desean recuperar.
    Qué retorna: Una lista de diccionarios de tareas (list[dict]) o una lista vacía ([]).
    """
    query = "SELECT id, title, description, completed, owner_id, created_at, completed_at FROM tasks WHERE owner_id = %s"
    tasks = execute_query(query, (owner_id,), fetch_all=True)
    
    # Si la consulta falla, retorna None, lo convertimos a lista vacía para consistencia
    return tasks if tasks is not None else []

def get_task_by_id(task_id: int, owner_id: int):
    """
    Propósito: Recuperar una tarea específica por su ID, asegurando que pertenezca al usuario.
    Parámetros de entrada:
        - task_id (int): ID de la tarea a buscar.
        - owner_id (int): ID del usuario dueño (para verificar propiedad).
    Qué retorna: Un diccionario con los datos de la tarea si existe y pertenece al usuario, o None.
    """
    query = "SELECT id, title, description, completed, owner_id, created_at, completed_at FROM tasks WHERE id = %s AND owner_id = %s"
    task = execute_query(query, (task_id, owner_id), fetch_one=True)
    return task

def update_task(task_id: int, owner_id: int, task: TaskUpdate):
    """
    Propósito: Actualizar los campos de una tarea existente, verificando la propiedad.
    Parámetros de entrada:
        - task_id (int): ID de la tarea a actualizar.
        - owner_id (int): ID del usuario dueño.
        - task (TaskUpdate): Modelo Pydantic con los campos a actualizar.
    Qué retorna: True si la actualización fue exitosa, False en caso contrario.
    """
    # 1. Obtener la tarea actual para construir el query
    current_task = get_task_by_id(task_id, owner_id)
    if not current_task:
        return False # No existe o no pertenece al usuario

    # 2. Construir la consulta de forma dinámica
    updates = []
    params = []
    
    if task.title is not None:
        updates.append("title = %s")
        params.append(task.title)
    if task.description is not None:
        updates.append("description = %s")
        params.append(task.description)
    if task.completed is not None:
        updates.append("completed = %s")
        params.append(task.completed)
        # Ajustamos completed_at según el estado
        if task.completed:
            updates.append("completed_at = NOW()")
        else:
            updates.append("completed_at = NULL")

    if not updates:
        # No hay campos para actualizar
        return True 

    # 3. Ejecutar el UPDATE
    set_clause = ", ".join(updates)
    query = f"UPDATE tasks SET {set_clause} WHERE id = %s AND owner_id = %s"
    params.extend([task_id, owner_id]) # Añadir ID y owner_id al final de los parámetros

    result = execute_query(query, tuple(params))
    
    if result is True:
        logger.info(f"Tarea ID {task_id} actualizada por el usuario {owner_id}.")
    else:
        logger.error(f"Fallo al actualizar la Tarea ID {task_id} para el usuario {owner_id}.")
    
    return result is True

def delete_task(task_id: int, owner_id: int):
    """
    Propósito: Eliminar una tarea de la base de datos, verificando la propiedad.
    Parámetros de entrada:
        - task_id (int): ID de la tarea a eliminar.
        - owner_id (int): ID del usuario dueño.
    Qué retorna: True si la eliminación fue exitosa, False en caso contrario.
    """
    query = "DELETE FROM tasks WHERE id = %s AND owner_id = %s"
    params = (task_id, owner_id)

    result = execute_query(query, params)
    
    if result is True:
        logger.info(f"Tarea ID {task_id} eliminada por el usuario {owner_id}.")
    else:
        logger.error(f"Fallo al eliminar la Tarea ID {task_id} para el usuario {owner_id}.")
        
    return result is True

