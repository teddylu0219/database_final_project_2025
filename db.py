import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """
    Create and return a database connection
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'nycu_food'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            cursor_factory=RealDictCursor
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    """
    Execute a SQL query and return results

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE/DELETE)

    Returns:
        For SELECT queries: list of dict rows
        For INSERT/UPDATE/DELETE: None
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(query, params)

        if fetch:
            results = cur.fetchall()
            return results
        else:
            conn.commit()
            return None
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Query execution error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def execute_query_one(query, params=None):
    """
    Execute a SQL query and return a single result

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)

    Returns:
        Single dict row or None
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(query, params)
        result = cur.fetchone()
        return result
    except psycopg2.Error as e:
        print(f"Query execution error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def init_db():
    """
    Initialize database with schema only.
    Data should be loaded via load_all.sh or /import.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print("Creating database schema...")
        with open('schema.sql', 'r', encoding='utf-8') as f:
            cur.execute(f.read())

        conn.commit()
        print("Database schema created. Load data via load_all.sh or /import.")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database initialization error: {e}")
        raise
    except FileNotFoundError as e:
        print(f"SQL file not found: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    # Test database connection
    try:
        conn = get_db_connection()
        print("Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {e}")
