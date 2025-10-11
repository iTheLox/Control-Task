from app.database import execute_query

def get_user_by_username(username: str):
    query = "SELECT * FROM users WHERE username = %s"
    return execute_query(query, (username,), fetch_one=True)

def get_user_by_email(email: str):
    query = "SELECT * FROM users WHERE email = %s"
    return execute_query(query, (email,), fetch_one=True)

def create_user(username: str, email: str, hashed_password: str):
    query = """
    INSERT INTO users (username, email, hashed_password)
    VALUES (%s, %s, %s)
    """
    result = execute_query(query, (username, email, hashed_password))
    return result is not None
