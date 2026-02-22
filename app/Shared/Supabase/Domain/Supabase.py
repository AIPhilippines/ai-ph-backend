from supabase import create_client, Client
from typing import Any
from uuid import UUID
from app.settings import SUPABASE_URL, SUPABASE_KEY

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