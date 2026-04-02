import psycopg2
from psycopg2 import OperationalError, DatabaseError
from dotenv import load_dotenv
import os

load_dotenv()

class PostgresDB:
    def __init__(self):
        self.host     = os.getenv("DB_HOST")
        self.port     = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.conn     = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
            )
        except OperationalError as e:
            raise OperationalError(f"Failed to connect to database: {e}")
        except DatabaseError as e:
            raise DatabaseError(f"Database error during connection: {e}")

    def execute_query(self, query, params=None, fetch_all=False):
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            result = cur.fetchall() if fetch_all else cur.fetchone()
            cur.close()
            return result
        except Exception as e:
            raise Exception(f"Query execution error: {e}")

    def execute_insert_update_delete(self, query, params=None):
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            result = cur.fetchall() if cur.description is not None else cur.rowcount
            self.conn.commit()
            cur.close()
            return result
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Insert/Update/Delete error: {e}")