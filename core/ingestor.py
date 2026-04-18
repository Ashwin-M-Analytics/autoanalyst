# core/ingestor.py

import pandas as pd
import sqlite3
import os
import re


def sanitize_table_name(filename: str) -> str:
    """Convert filename to a valid SQL table name."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name.lower()


def sanitize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for SQL compatibility."""
    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", col).strip("_").lower()
        for col in df.columns
    ]
    return df


def get_session_db_path(session_id: str) -> str:
    """
    Build a per-session DB path so two users never share the same file.
    """
    os.makedirs("db", exist_ok=True)
    return f"db/session_{session_id}.db"


def ingest_csv(uploaded_file, session_id: str) -> tuple[str, pd.DataFrame, str]:
    """
    Takes a Streamlit UploadedFile object and a unique session_id.
    Returns: (table_name, dataframe, db_path)
    """
    db_path = get_session_db_path(session_id)

    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding="latin-1")

    df = sanitize_column_names(df)
    table_name = sanitize_table_name(uploaded_file.name)

    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    return table_name, df, db_path