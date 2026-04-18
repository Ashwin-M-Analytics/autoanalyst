# AutoAnalyst

**Ask any business question about your data — no SQL required.**

AutoAnalyst is a conversational BI tool that turns plain-English questions into SQL queries, executes them on your uploaded CSV, and returns results with auto-generated charts and business insights.

---

## What it does

1. **Upload** a CSV file
2. **Ask** a question in plain English (e.g. *"Which car has the highest horsepower?"*)
3. **Get back** the SQL query, a result table, a chart, and a written insight — in seconds

No SQL knowledge needed. No data science team needed.

---

## Features

- **Natural language to SQL** — powered by Llama 3.3 70B via Groq
- **Schema-aware prompting** — the LLM sees column types *and* sample values for accurate queries
- **Safety guardrails** — only read-only SELECT queries are executed; destructive queries are blocked
- **Auto-retry** — if a query fails, the LLM sees the error and fixes its own SQL
- **Smart charts** — automatically picks the best Plotly chart type (bar, line, scatter, heatmap, donut, violin, funnel, time-series, or histogram) based on the data shape
- **Business insights** — every result comes with a 2–3 sentence plain-English summary
- **Per-session databases** — each user gets an isolated SQLite DB, so no collisions
- **Query caching** — repeated questions return instantly without re-calling the LLM
- **Query history** — all past questions and their SQL are saved in the sidebar

---

## Tech stack

| Layer        | Tool                          |
|--------------|-------------------------------|
| Frontend     | Streamlit                     |
| LLM          | Llama 3.3 70B (via Groq API)  |
| Orchestration| LangChain                     |
| Database     | SQLite                        |
| Charts       | Plotly                        |
| Data         | Pandas                        |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Ashwin-M-Analytics/autoanalyst.git
cd autoanalyst
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Get a free API key from [console.groq.com](https://console.groq.com), then create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Project structure

```
autoanalyst/
├── app.py                      # Streamlit UI and main entry point
├── requirements.txt            # Python dependencies
├── .env                        # API keys (gitignored)
├── core/
│   ├── ingestor.py             # CSV to SQLite ingestion
│   ├── sql_generator.py        # LLM prompt + safety guard + retry
│   ├── executor.py             # SQL execution on SQLite
│   ├── chart_builder.py        # Auto chart-type selection
│   └── insight_generator.py    # Plain-English insights from results
└── utils/
    └── schema_extractor.py     # Schema + sample rows for LLM prompts
```

---

## Example questions

Try these with any CSV:

- *"What are the top 5 rows by revenue?"*
- *"Show me average sales by region"*
- *"How does price relate to quantity?"*
- *"Which category has the most products?"*
- *"What's the trend over time?"*

---

## How it works

```
CSV upload
    ↓
Ingest into SQLite (per-session DB)
    ↓
Extract schema + sample rows
    ↓
User types a question
    ↓
LLM generates SQL → safety check → execute
    ↓                       ↓
    ↓               (on failure: retry with error)
    ↓
Result table + auto-chart + LLM-generated insight
```

---

## Safety

- Only `SELECT` queries are allowed — `DROP`, `DELETE`, `UPDATE`, etc. are blocked at the application layer
- No multi-statement queries (`;` is rejected)
- API keys are loaded from `.env` and never committed to git

---

## License

MIT
