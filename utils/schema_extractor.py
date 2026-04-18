# utils/schema_extractor.py

import sqlite3
import pandas as pd


def get_schema(db_path: str, table_name: str, n_samples: int = 3) -> str:
    """
    Returns a human-readable schema string for the LLM prompt,
    including a few sample rows so the model can see actual values.

    Example output:
        Table: sales_data
        Columns: region (TEXT), revenue (REAL), month (TEXT), units (INTEGER)
        Sample rows:
          region='North', revenue=12450.5, month='2024-01', units=120
          region='South', revenue=9800.0,  month='2024-01', units=95
          region='East',  revenue=15230.2, month='2024-01', units=140
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    col_descriptions = ", ".join(
        f"{col[1]} ({col[2]})" for col in columns
    )

    # Fetch a few sample rows for the LLM
    try:
        sample_df = pd.read_sql_query(
            f"SELECT * FROM {table_name} LIMIT {n_samples};", conn
        )
    except Exception:
        sample_df = pd.DataFrame()
    finally:
        conn.close()

    schema_str = f"Table: {table_name}\nColumns: {col_descriptions}"

    if not sample_df.empty:
        sample_lines = []
        for _, row in sample_df.iterrows():
            pairs = []
            for col, val in row.items():
                if isinstance(val, str):
                    pairs.append(f"{col}='{val}'")
                else:
                    pairs.append(f"{col}={val}")
            sample_lines.append("  " + ", ".join(pairs))
        schema_str += "\nSample rows:\n" + "\n".join(sample_lines)

    return schema_str