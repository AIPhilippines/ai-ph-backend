from supabase import create_client, Client
from typing import Any
from uuid import UUID
from app.settings import SUPABASE_URL, SUPABASE_KEY, DB_HOST, DB_NAME, DB_USER, DB_PORT, DB_PASSWORD
import psycopg2

class Supabase:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def insert_data(self, table_name: str, data: dict[str, Any]):
        self.client.table(table_name).insert(data).execute()

    def select_data(self, table_name: str, columns: list[str]):
        return self.client.table(table_name).select(*columns).execute()

    def update_data(self, table_name: str, data: dict[str, Any], id: UUID):
        self.client.table(table_name).update(data).eq("id", id).execute()

    def delete_data(self, table_name: str, id: UUID):
        self.client.table(table_name).delete().eq("id", id).execute()

    def execute_sql(self, query: str, params: tuple = None):
        """Executes a raw SQL query using psycopg2. Useful for migrations."""
        if not DB_PASSWORD:
            raise RuntimeError("DB_PASSWORD is not set in environment variables")
            
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=int(DB_PORT),
            sslmode="require"
        )
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                if cur.description: # If it's a SELECT or has RETURNING
                    return cur.fetchall()
                return None
        finally:
            conn.close()
