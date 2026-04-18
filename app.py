# app.py

import uuid
import streamlit as st

from core.ingestor import ingest_csv
from utils.schema_extractor import get_schema
from core.sql_generator import generate_sql_with_retry
from core.chart_builder import build_chart
from core.insight_generator import generate_insight

st.set_page_config(page_title="AutoAnalyst", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500&family=DM+Sans:wght@400;600&display=swap');

    .stApp { background-color: #ffffff; }
    .stApp, .stApp * { color: #1a1a2e !important; }

    h1 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500 !important;
        font-size: 2.8rem !important;
        letter-spacing: -1px;
        color: #1a1a2e !important;
    }
    .stCaption p {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 300 !important;
        font-size: 1rem !important;
        color: #555555 !important;
    }
    h2, h3 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 400 !important;
        color: #1a1a2e !important;
    }
    h3 {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    [data-testid="stInfo"] {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 400 !important;
        font-size: 2.5rem !important;
        line-height: 2.0 !important;
        background: linear-gradient(135deg, #eef2ff, #f0fdf4) !important;
        border-left: 5px solid #4361ee !important;
        border-radius: 10px !important;
        color: #1a1a2e !important;
        padding: 20px !important;
    }
    [data-testid="stExpander"] {
        background-color: #f8f9ff !important;
        border: 1px solid #e0e7ff !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] * {
        color: #1a1a2e !important;
        background-color: transparent !important;
    }
    [data-testid="stExpander"] code { background-color: #eef2ff !important; }
    [data-testid="stFileUploader"] {
        background: #f0f4ff;
        border: 2px dashed #4361ee;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #f0f4ff !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] * { color: #1a1a2e !important; }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #4361ee !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }
    [data-testid="stTextInput"] input {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 400 !important;
        font-size: 1.5rem !important;
        padding: 14px 16px !important;
        border: 2px solid #4361ee !important;
        border-radius: 10px !important;
        background: #f8f9ff !important;
        color: #1a1a2e !important;
        caret-color: #4361ee !important;
    }
    [data-testid="stAlert"] { border-radius: 10px; }
    [data-testid="stSidebar"] { background: #1a1a2e !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] code {
        background: #2a2a4e !important;
        color: #a8d8ff !important;
    }
    hr { border-color: #e0e7ff !important; }
    [data-testid="stDownloadButton"] button {
        background: #4361ee !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    [data-testid="stFormSubmitButton"] button {
        background: #4361ee !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #e0e7ff;
        border-radius: 10px;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)


# --- Header ---
st.title("AutoAnalyst")
st.caption("Ask any business question about your data — no SQL required.")


# --- Session state init ---
# Each browser session gets its own isolated DB file via this UUID.
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
if "table_name" not in st.session_state:
    st.session_state.table_name = None
if "db_path" not in st.session_state:
    st.session_state.db_path = None
if "schema" not in st.session_state:
    st.session_state.schema = None
if "history" not in st.session_state:
    st.session_state.history = []


# --- Cached LLM wrappers ---
# Cache keyed on the arguments so repeated questions are instant and free.
@st.cache_data(show_spinner=False)
def cached_generate_sql_with_retry(schema: str, question: str, db_path: str):
    return generate_sql_with_retry(schema, question, db_path)


@st.cache_data(show_spinner=False)
def cached_generate_insight(question: str, sql: str, result_csv: str) -> str:
    import pandas as pd
    from io import StringIO
    df = pd.read_csv(StringIO(result_csv)) if result_csv else pd.DataFrame()
    return generate_insight(question, sql, df)


# --- Sidebar: Query History ---
with st.sidebar:
    st.header("🕓 Query History")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            st.markdown(f"**{i+1}.** {item['question']}")
            st.code(item['sql'], language="sql")
            st.divider()
    else:
        st.caption("Your past questions will appear here.")


# --- CSV Upload ---
st.subheader("Upload your data")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    with st.spinner("Ingesting CSV into database..."):
        table_name, df, db_path = ingest_csv(
            uploaded_file,
            session_id=st.session_state.session_id,
        )
        st.session_state.table_name = table_name
        st.session_state.db_path = db_path
        st.session_state.schema = get_schema(db_path, table_name)

    st.success(
        f"✅ Loaded as table: `{table_name}` "
        f"({len(df)} rows, {len(df.columns)} columns)"
    )

    with st.expander("Preview data"):
        st.dataframe(df.head(10), use_container_width=True)

    with st.expander("Detected schema (what the LLM will see)"):
        st.code(st.session_state.schema)


# --- Question Input (wrapped in a form so it only fires on submit) ---
if st.session_state.table_name:
    st.divider()
    st.subheader("Ask a business question")

    with st.form("question_form", clear_on_submit=False):
        question = st.text_input(
            "Type your question",
            placeholder="e.g. Which car has the highest horsepower?"
        )
        submitted = st.form_submit_button("Run")

    if submitted and question:
        with st.spinner("Generating SQL..."):
            sql, df_result, error = cached_generate_sql_with_retry(
                st.session_state.schema,
                question,
                st.session_state.db_path,
            )

        with st.expander("🔍 Generated SQL"):
            st.code(sql, language="sql")

        if error:
            st.error(f"SQL failed: {error}")
        else:
            st.session_state.history.append({
                "question": question,
                "sql": sql,
            })

            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Query Result")
                st.dataframe(df_result, use_container_width=True)
            with col2:
                st.download_button(
                    label="⬇️ Export as CSV",
                    data=df_result.to_csv(index=False),
                    file_name="result.csv",
                    mime="text/csv",
                )

            st.divider()

            # --- Chart ---
            fig = build_chart(df_result)
            if fig:
                st.subheader("Chart")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Could not generate a chart for this result.")

            st.divider()

            # --- Insight (cached on question + sql + result) ---
            with st.spinner("Generating insight..."):
                insight = cached_generate_insight(
                    question,
                    sql,
                    df_result.to_csv(index=False),
                )
            st.subheader("What This Means:")
            st.info(insight)