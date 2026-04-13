# app.py

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

    /* ── Background & Base ── */
    .stApp {
        background-color: #ffffff;
    }

    /* ── Force dark text everywhere ── */
    .stApp, .stApp * {
        color: #1a1a2e !important;
    }

    /* ── Main Title — Poppins Medium 500 ── */
    h1 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500 !important;
        font-size: 2.8rem !important;
        letter-spacing: -1px;
        color: #1a1a2e !important;
    }

    /* ── Caption — Poppins Light 300 ── */
    .stCaption p {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 300 !important;
        font-size: 1rem !important;
        color: #555555 !important;
    }

    /* ── Section Subheaders (Upload, Ask) — Poppins Regular 400 ── */
    h2, h3 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 400 !important;
        color: #1a1a2e !important;
    }

    /* ── Business Insight, Chart, Query Result labels — DM Sans SemiBold 600 ── */
    h3 {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
    }

    /* ── Business Insight content — DM Sans Regular 400 ── */
    /* ↓ CHANGE font-size here to adjust insight text size */
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

    /* ── Expander background + text when open ── */
    [data-testid="stExpander"] {
        background-color: #f8f9ff !important;
        border: 1px solid #e0e7ff !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] * {
        color: #1a1a2e !important;
        background-color: transparent !important;
    }
    [data-testid="stExpander"] code {
        background-color: #eef2ff !important;
    }

    /* ── File Uploader outer ── */
    [data-testid="stFileUploader"] {
        background: #f0f4ff;
        border: 2px dashed #4361ee;
        border-radius: 12px;
        padding: 16px;
    }

    /* ── File Uploader inner dropzone ── */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #f0f4ff !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #1a1a2e !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #4361ee !important;
        color: #ffffff !important;
        border-radius: 6px !important;
    }

    /* ── Question Input ── */
    /* ↓ CHANGE font-size here to adjust question box text size */
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

    /* ── Success Box ── */
    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #1a1a2e !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] code {
        background: #2a2a4e !important;
        color: #a8d8ff !important;
    }

    /* ── Divider ── */
    hr {
        border-color: #e0e7ff !important;
    }

    /* ── Download Button ── */
    [data-testid="stDownloadButton"] button {
        background: #4361ee !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }

    /* ── Dataframe ── */
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
if "table_name" not in st.session_state:
    st.session_state.table_name = None
if "db_path" not in st.session_state:
    st.session_state.db_path = None
if "schema" not in st.session_state:
    st.session_state.schema = None
if "history" not in st.session_state:
    st.session_state.history = []

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
        table_name, df, db_path = ingest_csv(uploaded_file)
        st.session_state.table_name = table_name
        st.session_state.db_path = db_path
        st.session_state.schema = get_schema(db_path, table_name)

    st.success(f"✅ Loaded as table: `{table_name}` ({len(df)} rows, {len(df.columns)} columns)")

    with st.expander("Preview data"):
        st.dataframe(df.head(10), use_container_width=True)

    with st.expander("Detected schema (what the LLM will see)"):
        st.code(st.session_state.schema)

# --- Question Input ---
if st.session_state.table_name:
    st.divider()
    st.subheader("Ask a business question")
    question = st.text_input(
        "Type your question",
        placeholder="e.g. Which car has the highest horsepower?"
    )

    if question:
        with st.spinner("Generating SQL..."):
            sql, df_result, error = generate_sql_with_retry(
                st.session_state.schema,
                question,
                st.session_state.db_path
            )

        with st.expander("🔍 Generated SQL"):
            st.code(sql, language="sql")

        if error:
            st.error(f"SQL failed after retry: {error}")
        else:
            st.session_state.history.append({
                "question": question,
                "sql": sql
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
                    mime="text/csv"
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

            # --- Insight ---
            with st.spinner("Generating insight..."):
                insight = generate_insight(question, sql, df_result)
            st.subheader("What This Means:")
            st.info(insight)