import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from config import Config

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        yield conn
    except Error as e:
        print(f"Database connection failed: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            yield cursor
            if commit:
                conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
