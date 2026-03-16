import psycopg2
from psycopg2 import OperationalError, DatabaseError
from dotenv import load_dotenv
import os

class PostgresDB:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PostgresDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        
        self.conn = None
        self._initialized = True
        
    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _connect(self):
        if self.conn:
            return self.conn
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
            )
            return self.conn
        except OperationalError as e:
            raise OperationalError(f"Failed to connect to database: {e}")
        except DatabaseError as e:
            raise DatabaseError(f"Database error during connection: {e}")

    def execute_query(self, query, params=None, fetch_all=False):
        conn = None
        try:
            conn = self.conn
            cur = conn.cursor()
            cur.execute(query, params)
            
            if fetch_all:
                result = cur.fetchall()
            else:
                result = cur.fetchone()
            
            cur.close()
            
            return result
        except Exception as e:
            raise Exception(f"Query execution error: {e}")

    def execute_insert_update_delete(self, query, params=None):
        conn = None
        try:
            conn = self.conn
            cur = conn.cursor()
        
            cur.execute(query, params)

            result = None

            if cur.description is not None:
                result = cur.fetchall()
            else:
                result = cur.rowcount

            conn.commit()
            cur.close()

            return result

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Insert/Update/Delete error: {e}")
        