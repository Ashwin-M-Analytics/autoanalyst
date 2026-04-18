# core/executor.py

import sqlite3
import pandas as pd


def execute_sql(db_path: str, sql: str) -> tuple[pd.DataFrame, str | None]:
    """
    Runs the SQL query on the SQLite database.
    Returns: (dataframe, error_message)
    If successful -> (df, None)
    If failed     -> (empty df, error string)
    """
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)