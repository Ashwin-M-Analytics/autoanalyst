# core/chart_builder.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORS = ["#4361ee", "#f72585", "#4cc9f0", "#7209b7", "#06d6a0", "#ffd166", "#ef476f"]


# ── Styling ────────────────────────────────────────────────────────────────────

def _style(fig) -> go.Figure:
    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="DM Sans, sans-serif", color="#1a1a2e", size=13),
        title_font=dict(family="DM Sans, sans-serif", size=16, color="#1a1a2e"),
        xaxis=dict(
            tickfont=dict(color="#1a1a2e", size=12),
            title_font=dict(color="#1a1a2e"),
            gridcolor="#e0e7ff",
            linecolor="#e0e7ff",
        ),
        yaxis=dict(
            tickfont=dict(color="#1a1a2e", size=12),
            title_font=dict(color="#1a1a2e"),
            gridcolor="#e0e7ff",
            linecolor="#e0e7ff",
        ),
        legend=dict(
            font=dict(color="#1a1a2e"),
            title_font=dict(color="#1a1a2e"),
        ),
        showlegend=True,
        margin=dict(t=60, b=40, l=40, r=40),
    )
    return fig


# ── Column Detection ───────────────────────────────────────────────────────────

def _detect_columns(df: pd.DataFrame):
    """
    Returns (numeric_cols, categorical_cols, datetime_cols)
    after attempting safe datetime conversion on object columns.
    """
    df = df.copy()

    for col in df.select_dtypes(include="object").columns:
        try:
            converted = pd.to_datetime(df[col], infer_datetime_format=True)
            df[col] = converted
        except Exception:
            pass

    datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [
        col for col in df.columns
        if col not in datetime_cols and col not in numeric_cols
    ]

    return df, numeric_cols, categorical_cols, datetime_cols


# ── Chart Builders ─────────────────────────────────────────────────────────────

def _histogram(df, col):
    fig = px.histogram(
        df, x=col,
        title=f"Distribution of {col}",
        color_discrete_sequence=COLORS,
        nbins=30,
    )
    return _style(fig)


def _bar_value_counts(df, col):
    counts = df[col].value_counts().reset_index()
    counts.columns = [col, "count"]
    fig = px.bar(
        counts, x=col, y="count",
        title=f"Count by {col}",
        color=col,
        color_discrete_sequence=COLORS,
    )
    return _style(fig)


def _time_series(df, datetime_col, numeric_col):
    df_sorted = df[[datetime_col, numeric_col]].sort_values(datetime_col)
    fig = px.line(
        df_sorted, x=datetime_col, y=numeric_col,
        title=f"{numeric_col} over time",
        color_discrete_sequence=COLORS,
    )
    fig.update_traces(mode="lines+markers")
    return _style(fig)


def _scatter(df, col_x, col_y):
    fig = px.scatter(
        df, x=col_x, y=col_y,
        title=f"{col_y} vs {col_x}",
        color_discrete_sequence=COLORS,
        trendline="ols",
        trendline_color_override="#f72585",
    )
    return _style(fig)


def _donut(df, cat_col, num_col):
    fig = px.pie(
        df, names=cat_col, values=num_col,
        title=f"{num_col} by {cat_col}",
        color_discrete_sequence=COLORS,
        hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _style(fig)


def _funnel(df, cat_col, num_col):
    df_sorted = df.sort_values(num_col, ascending=False)
    fig = px.funnel(
        df_sorted, y=cat_col, x=num_col,
        title=f"{num_col} by {cat_col}",
        color_discrete_sequence=COLORS,
    )
    return _style(fig)


def _violin(df, cat_col, num_col):
    fig = px.violin(
        df, x=cat_col, y=num_col,
        title=f"Distribution of {num_col} by {cat_col}",
        color=cat_col,
        color_discrete_sequence=COLORS,
        box=True,
        points="outliers",
    )
    return _style(fig)


def _heatmap(df, cat_col_1, cat_col_2, num_col):
    pivot = df.pivot_table(
        index=cat_col_1,
        columns=cat_col_2,
        values=num_col,
        aggfunc="mean",
    )
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="Blues",
        hoverongaps=False,
    ))
    fig.update_layout(title=f"{num_col} by {cat_col_1} and {cat_col_2}")
    return _style(fig)


def _bar(df, cat_col, num_col):
    df_sorted = df.sort_values(num_col, ascending=False)
    fig = px.bar(
        df_sorted, x=cat_col, y=num_col,
        title=f"{num_col} by {cat_col}",
        color=cat_col,
        color_discrete_sequence=COLORS,
    )
    return _style(fig)


def _line(df, col_x, col_y):
    df_sorted = df.sort_values(col_x)
    fig = px.line(
        df_sorted, x=col_x, y=col_y,
        title=f"{col_y} by {col_x}",
        color_discrete_sequence=COLORS,
    )
    return _style(fig)


# ── Main Entry Point ───────────────────────────────────────────────────────────

def build_chart(df: pd.DataFrame):
    """
    Automatically selects and returns the best Plotly chart
    for the given DataFrame. Returns None if no chart is possible.
    """

    # Safety checks
    if df is None or df.empty:
        return None

    # Work on a copy — never mutate original
    df, numeric_cols, categorical_cols, datetime_cols = _detect_columns(df)

    total_cols = len(df.columns)

    # ── A. SINGLE COLUMN ──────────────────────────────────────────────────────
    if total_cols == 1:
        if numeric_cols:
            return _histogram(df, numeric_cols[0])
        if categorical_cols:
            return _bar_value_counts(df, categorical_cols[0])
        return None

    # ── B. TIME SERIES (highest priority) ────────────────────────────────────
    if datetime_cols and numeric_cols:
        return _time_series(df, datetime_cols[0], numeric_cols[0])

    # ── C. NUMERIC RELATIONSHIP (scatter) ────────────────────────────────────
    if len(numeric_cols) >= 2 and not categorical_cols and not datetime_cols:
        col_x = numeric_cols[0]
        col_y = max(
            [c for c in numeric_cols if c != col_x],
            key=lambda c: df[c].nunique()
        )
        return _scatter(df, col_x, col_y)

    # ── D. CATEGORICAL + NUMERIC ──────────────────────────────────────────────
    if not numeric_cols:
        return None

    # Pick best numeric Y: highest unique count = real metric
    col_y = max(numeric_cols, key=lambda c: df[c].nunique())

    # D1. Two categorical columns + numeric → heatmap
    if len(categorical_cols) >= 2:
        cat_1 = categorical_cols[0]
        cat_2 = categorical_cols[1]
        rows = df[cat_1].nunique()
        cols = df[cat_2].nunique()
        if rows <= 20 and cols <= 20:
            agg = df.groupby([cat_1, cat_2])[col_y].mean().reset_index()
            return _heatmap(agg, cat_1, cat_2, col_y)

    # Single categorical column from here
    if not categorical_cols:
        # Fallback: treat lowest-unique numeric as X
        remaining = [c for c in numeric_cols if c != col_y]
        if remaining:
            return _line(df, remaining[0], col_y)
        return None

    col_x = categorical_cols[0]

    # Aggregate duplicates
    agg_df = df.groupby(col_x)[col_y].mean().reset_index()
    n_categories = agg_df[col_x].nunique()

    # D2. ≤ 3 categories → donut
    if n_categories <= 3:
        return _donut(agg_df, col_x, col_y)

    # D3. Funnel keyword detection
    funnel_keywords = ["stage", "step", "phase", "funnel", "level", "rank", "order"]
    if any(kw in col_x.lower() for kw in funnel_keywords):
        return _funnel(agg_df, col_x, col_y)

    # D4. Violin: many Y values per category (distribution analysis)
    y_unique = df[col_y].nunique()
    if y_unique > 15 and n_categories <= 10 and len(df) >= 20:
        return _violin(df, col_x, col_y)

    # D5. Bar: up to 20 categories
    if n_categories <= 20:
        return _bar(agg_df, col_x, col_y)

    # D6. Line: too many categories, treat as continuous
    return _line(agg_df, col_x, col_y)