# utils/schema_extractor.py

import sqlite3

def get_schema(db_path: str, table_name: str) -> str:
    """
    Returns a human-readable schema string for the LLM prompt.
    Example output:
        Table: sales_data
        Columns: region (TEXT), revenue (REAL), month (TEXT), units (INTEGER)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    conn.close()

    col_descriptions = ", ".join(
        f"{col[1]} ({col[2]})" for col in columns
    )
    return f"Table: {table_name}\nColumns: {col_descriptions}"