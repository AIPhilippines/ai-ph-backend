import os
import sys
import datetime
from app.Shared.Supabase.Domain.Supabase import Supabase

MIGRATIONS_DIR = "migrations"
MIGRATIONS_TABLE = "_migrations"

def init_db(db: Supabase):
    query = f"""
    CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    db.execute_sql(query)

def generate_migration(description: str, query: str = ""):
    if not os.path.exists(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR)
        print(f"Created directory: {MIGRATIONS_DIR}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{description.replace(' ', '_')}.py"
    filepath = os.path.join(MIGRATIONS_DIR, filename)

    content = f'''
def upgrade(db):
    """
    {description}
    """
    query = """
    {query}
    """
    db.execute_sql(query)
'''
    with open(filepath, "w") as f:
        f.write(content.strip())
    
    print(f"Generated migration: {filepath}")

def run_migrations():
    db = Supabase()
    init_db(db)

    if not os.path.exists(MIGRATIONS_DIR):
        print("No migrations directory found.")
        return

    executed = db.execute_sql(f"SELECT name FROM {MIGRATIONS_TABLE}")
    executed_names = {row[0] for row in executed} if executed else set()

    files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".py")])
    
    pending = [f for f in files if f not in executed_names]

    if not pending:
        print("No pending migrations.")
        return

    for filename in pending:
        print(f"Running migration: {filename}...")
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        
        import importlib.util
        spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        try:
            module.upgrade(db)
            
            db.execute_sql(f"INSERT INTO {MIGRATIONS_TABLE} (name) VALUES (%s)", (filename,))
            print(f"Successfully ran {filename}")
        except Exception as e:
            print(f"Error running migration {filename}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [run|generate] [description] [query]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run_migrations()
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Usage: python migrate.py generate <description> [query]")
            sys.exit(1)
        description = sys.argv[2]
        query = sys.argv[3] if len(sys.argv) > 3 else "-- Add your query here"
        generate_migration(description, query)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
