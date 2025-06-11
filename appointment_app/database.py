import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from config import Config

def _get_connection(config, database=None):
    """Internal function to create a database connection."""
    db_config = config.copy()
    if database:
        db_config['database'] = database
    return mysql.connector.connect(**db_config)

@contextmanager
def get_db_connection(database=None, use_call_db=False):
    """Get a database connection.
    
    Args:
        database (str, optional): Name of the database to connect to. Defaults to None.
        use_call_db (bool): If True, use the call history database config. Defaults to False.
    """
    conn = None
    try:
        if database=="call_history":
            config = Config.CALL_HISTORY_DB_CONFIG
        else:
            config = Config.DB_CONFIG

        conn = _get_connection(config, database)
        yield conn
    except Error as e:
        db_type = "call history" if use_call_db else "main"
        print(f"{db_type.capitalize()} database connection failed: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

@contextmanager
def get_db_cursor(commit=False, database=None, dictionary=True, use_call_db=False):
    """Get a database cursor.
    
    Args:
        commit (bool): Whether to commit the transaction. Defaults to False.
        database (str, optional): Name of the database to connect to. Defaults to None.
        dictionary (bool): Whether to return results as dictionaries. Defaults to True.
        use_call_db (bool): If True, use the call history database. Defaults to False.
    """
    with get_db_connection(database, use_call_db=use_call_db) as conn:
        cursor = None
        try:
            cursor = conn.cursor(dictionary=dictionary)
            yield cursor
            if commit:
                conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            db_type = "call history" if use_call_db else "main"
            print(f"{db_type.capitalize()} database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
