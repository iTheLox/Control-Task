import os
import shutil
from fastapi import APIRouter, UploadFile, HTTPException
from celery.result import AsyncResult
from app.celery_worker import celery
from app.task import bulk_upload

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-xls")
async def upload_xls(file: UploadFile):
    if not file.filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Archivo no soportado. Use .xls o .xlsx")
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task = bulk_upload.delay(dest)
    return {"task_id": task.id, "status": "processing"}

@router.get("/upload-status/{task_id}")
async def upload_status(task_id: str):
    task = AsyncResult(task_id, app=celery)
    if task.state == "PENDING":
        return {"state": "PENDING"}
    if task.state == "PROGRESS":
        return {"state": "PROGRESS", **(task.info or {})}
    if task.state == "SUCCESS":
        return {"state": "COMPLETED", "result": task.result}
    if task.state == "FAILURE":
        return {"state": "FAILED", "error": str(task.result)}
    return {"state": task.state}
