import mysql.connector
import os
import logging
from dotenv import load_dotenv

# Carga variables de entorno para la prueba LOCAL. Docker usa las variables del contenedor.
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la conexión desde las variables de entorno
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"), # 'db' en Docker, '127.0.0.1' localmente
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}

def get_db_connection():
    """
    Propósito: Establecer y retornar una nueva conexión a la base de datos MySQL.
    Parámetros de entrada: Ninguno.
    Qué retorna: Un objeto de conexión a MySQL (`mysql.connector.connection.MySQLConnection`).
                 Retorna None si la conexión falla.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        logger.info("Conexión a MySQL establecida con éxito.")
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Error al conectar a MySQL: {err}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al intentar conectar: {e}")
        return None

def execute_query(sql_query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    """
    Propósito: Ejecutar una consulta SQL (SELECT, INSERT, UPDATE, DELETE) de manera segura.
    Parámetros de entrada:
        - sql_query (str): La consulta SQL a ejecutar.
        - params (tuple): Tupla de parámetros para la consulta, para evitar inyección SQL.
        - fetch_one (bool): Si es True, retorna solo la primera fila (para SELECT).
        - fetch_all (bool): Si es True, retorna todas las filas (para SELECT).
    Qué retorna:
        - Para INSERT/UPDATE/DELETE: El ID insertado (si es INSERT) o True/False (éxito/fallo).
        - Para SELECT con fetch_one: La primera fila (dict) o None.
        - Para SELECT con fetch_all: Una lista de filas (list[dict]) o una lista vacía.
    """
    connection = None
    cursor = None
    result = None
    try:
        connection = get_db_connection()
        if connection is None:
            raise Exception("No se pudo obtener la conexión a la base de datos.")

        # Usar dictionary=True para obtener resultados como diccionarios
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql_query, params)

        if sql_query.strip().upper().startswith("SELECT"):
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = True # Caso de SELECT sin fetch
        else:
            connection.commit()
            if sql_query.strip().upper().startswith("INSERT"):
                result = cursor.lastrowid # Retorna el ID de la última fila insertada
            else:
                result = True # Retorna True para UPDATE/DELETE exitosos

    except mysql.connector.Error as err:
        logger.error(f"Error de base de datos en la ejecución de la consulta '{sql_query[:50]}...': {err}")
        result = None

    except Exception as e:
        logger.error(f"Error inesperado al ejecutar la consulta: {e}")
        result = None

    finally:
        # Cierre seguro de la conexión y el cursor (Política de manejo de conexiones)
        if cursor:
            cursor.close()
        if connection:
            if connection.is_connected():
                connection.close()
                logger.info("Conexión a MySQL cerrada.")
        return result

def create_initial_tables():
    """
    Propósito: Crear las tablas iniciales de la base de datos (users y tasks) si no existen.
    Parámetros de entrada: Ninguno.
    Qué retorna: True si las tablas se crearon o ya existen, False en caso de error.
    """
    # Usar triple comilla para consultas multilinea
    user_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        hashed_password VARCHAR(255) NOT NULL
    )
    """
    task_table_query = """
    CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        completed BOOLEAN NOT NULL DEFAULT FALSE,
        owner_id INT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME DEFAULT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """
    result_user = execute_query(user_table_query)
    result_task = execute_query(task_table_query)

    if result_user is None or result_task is None:
        logger.error("Fallo al crear una o ambas tablas iniciales.")
        return False
    
    logger.info("Tablas de usuarios y tareas verificadas/creadas con éxito.")
    return True
