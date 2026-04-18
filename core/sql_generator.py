# core/sql_generator.py

import os
import re
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.executor import execute_sql

load_dotenv()

# Initialize the LLM -- reused across calls
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0  # deterministic, we want precise SQL
)

# ── Prompts ────────────────────────────────────────────────────────────────────

SQL_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
You are an expert SQL analyst. Given the table schema below, write a valid SQLite SQL query that answers the user's question.

Schema:
{schema}

Rules:
- Return ONLY the raw SQL query. No explanation, no markdown, no backticks.
- Use only the column names exactly as they appear in the schema.
- Always use the correct table name from the schema.
- If aggregating, always include a GROUP BY clause where needed.
- Only write SELECT queries. Never write DROP, DELETE, UPDATE, INSERT, ALTER, or CREATE.

Question: {question}

SQL:
"""
)

RETRY_PROMPT = PromptTemplate(
    input_variables=["schema", "question", "failed_sql", "error"],
    template="""
You previously wrote a SQL query that failed. Fix it.

Schema:
{schema}

Original question: {question}

Failed SQL:
{failed_sql}

Error from SQLite:
{error}

Rules:
- Return ONLY the corrected raw SQL query. No explanation, no markdown, no backticks.
- Only write SELECT queries.

Corrected SQL:
"""
)


# ── SQL Safety ─────────────────────────────────────────────────────────────────

FORBIDDEN_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter",
    "truncate", "create", "replace", "attach", "detach", "pragma",
]


def is_safe_select(sql: str) -> bool:
    """
    Guardrail: only allow read-only SELECT (or CTE) queries.
    Blocks anything that could modify the database.
    """
    if not sql:
        return False

    stripped = sql.strip().rstrip(";").lower()

    # Must start with SELECT or WITH (for CTEs)
    if not (stripped.startswith("select") or stripped.startswith("with")):
        return False

    # No multi-statement injection
    if ";" in stripped:
        return False

    # No destructive keywords as whole words
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", stripped):
            return False

    return True


# ── Core Functions ─────────────────────────────────────────────────────────────

def _clean_sql_output(raw: str) -> str:
    """Strip markdown fences and stray 'sql' prefix from LLM output."""
    sql = raw.strip().strip("`").strip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    return sql


def generate_sql(schema: str, question: str) -> str:
    chain = SQL_PROMPT | llm | StrOutputParser()
    raw = chain.invoke({"schema": schema, "question": question})
    return _clean_sql_output(raw)


def generate_sql_with_retry(
    schema: str,
    question: str,
    db_path: str,
) -> tuple[str, pd.DataFrame, str | None]:
    """
    Generates SQL, safety-checks it, and executes it.
    On failure, retries once with a dedicated retry prompt.
    Returns: (final_sql, dataframe, error)
    """
    # First attempt
    sql = generate_sql(schema, question)

    if not is_safe_select(sql):
        return sql, pd.DataFrame(), (
            "Blocked: generated query is not a safe SELECT statement."
        )

    df, error = execute_sql(db_path, sql)

    if error is None:
        return sql, df, None

    # Retry once with a proper retry prompt
    retry_chain = RETRY_PROMPT | llm | StrOutputParser()
    raw = retry_chain.invoke({
        "schema": schema,
        "question": question,
        "failed_sql": sql,
        "error": error,
    })
    retry_sql = _clean_sql_output(raw)

    if not is_safe_select(retry_sql):
        return retry_sql, pd.DataFrame(), (
            "Blocked: retried query is not a safe SELECT statement."
        )

    df, error = execute_sql(db_path, retry_sql)
    return retry_sql, df, error