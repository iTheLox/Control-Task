import os
import time
import pandas as pd
from app.celery_worker import celery
from app.database import get_db_connection

@celery.task(bind=True)
def bulk_upload(self, file_path):
    try:
        df = pd.read_excel(file_path)
        total = len(df) if df is not None else 0
        if total == 0:
            return {"status": "completed", "total": 0}

        conn = get_db_connection()
        if conn is None:
            raise Exception("No DB connection")

        cursor = conn.cursor()

        # Ajusta la query a tu tabla real (aquí asumo 'users' con columnas username,email)
        for i, row in df.iterrows():
            username = row.get('username') or row.get('nombre') or row.get('name')
            email = row.get('email') or row.get('correo')
            if not username or not email:
                # opcional: recoge errores en una lista
                continue

            cursor.execute(
                "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)",
                (str(username), str(email), "")  # hashed_password vacío: idealmente generar o pedir
            )

            if (i + 1) % 100 == 0:
                conn.commit()

            percent = int(((i + 1) / total) * 100)
            self.update_state(state="PROGRESS", meta={"current": i + 1, "total": total, "percent": percent})

        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "completed", "total": total}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
