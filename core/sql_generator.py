# core/sql_generator.py

import os
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Initialize the LLM — this is reused across calls
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0  # 0 = deterministic, no creativity — we want precise SQL
)

# The prompt template — schema and question are injected at runtime
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

Question: {question}

SQL:
"""
)

def generate_sql(schema: str, question: str) -> str:
    chain = SQL_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"schema": schema, "question": question})
    
    sql = result.strip().strip("```").strip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    
    return sql


def generate_sql_with_retry(schema: str, question: str, db_path: str) -> tuple[str, pd.DataFrame, str | None]:
    """
    Tries to generate and execute SQL.
    If it fails, feeds the error back to LLM and retries once.
    Returns: (final_sql, dataframe, error)
    """
    import sqlite3
    import pandas as pd

    def run(sql):
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            return df, None
        except Exception as e:
            return pd.DataFrame(), str(e)

    # First attempt
    sql = generate_sql(schema, question)
    df, error = run(sql)

    if error:
        # Retry with error context
        retry_prompt = f"""
The following SQL query failed with this error:
SQL: {sql}
Error: {error}

Fix the SQL so it works correctly for this schema:
{schema}

Return ONLY the corrected raw SQL query.
"""
        chain = SQL_PROMPT | llm | StrOutputParser()
        sql = chain.invoke({"schema": schema, "question": retry_prompt}).strip()
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()
        df, error = run(sql)

    return sql, df, error