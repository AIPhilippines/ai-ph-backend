def upgrade(db):
    query = """
    CREATE TABLE tests (id SERIAL PRIMARY KEY, name TEXT);
    """
    db.execute_sql(query)