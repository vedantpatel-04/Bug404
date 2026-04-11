"""
Reusable Plotly chart wrappers for the dashboard.
All charts use a consistent dark theme with the ShelfIQ color palette.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


# ─── Theme Constants ──────────────────────────────────────
DARK_BG = "#0f0f1a"
CARD_BG = "rgba(30, 30, 60, 0.7)"
GRID_COLOR = "rgba(255, 255, 255, 0.06)"
TEXT_COLOR = "#e8e8f0"
TEXT_SECONDARY = "#a0a0c0"
ACCENT_BLUE = "#4a9eff"
ACCENT_PURPLE = "#8b5cf6"
ACCENT_GREEN = "#22c55e"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_YELLOW = "#eab308"

COLOR_PALETTE = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED, ACCENT_YELLOW, "#06b6d4", "#ec4899"]


def _base_layout(title: str = "", height: int = 400) -> dict:
    """Base layout settings for all charts."""
    return dict(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=16), x=0.02) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY, size=12),
        margin=dict(l=50, r=30, t=50 if title else 20, b=50),
        height=height,
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_SECONDARY),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hoverlabel=dict(bgcolor=CARD_BG, font_color=TEXT_COLOR, bordercolor=GRID_COLOR),
    )


def line_chart(df: pd.DataFrame, x: str, y: str, title: str = "", color: str = ACCENT_BLUE,
               y_lower: str = None, y_upper: str = None, height: int = 400) -> go.Figure:
    """Create a line chart with optional confidence bands."""
    fig = go.Figure()

    # Confidence band
    if y_lower and y_upper and y_lower in df.columns and y_upper in df.columns:
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y_upper], mode="lines",
            line=dict(width=0), showlegend=False, name="Upper",
        ))
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y_lower], mode="lines",
            line=dict(width=0), fill="tonexty",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
            showlegend=False, name="Lower",
        ))

    # Main line
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y], mode="lines",
        line=dict(color=color, width=2.5),
        name=y.replace("_", " ").title(),
    ))

    fig.update_layout(**_base_layout(title, height))
    return fig


def multi_line_chart(df: pd.DataFrame, x: str, y_columns: list, title: str = "", height: int = 400) -> go.Figure:
    """Create a multi-line chart."""
    fig = go.Figure()
    for i, col in enumerate(y_columns):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], mode="lines",
            line=dict(color=COLOR_PALETTE[i % len(COLOR_PALETTE)], width=2),
            name=col.replace("_", " ").title(),
        ))
    fig.update_layout(**_base_layout(title, height))
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", color: str = ACCENT_BLUE, height: int = 400) -> go.Figure:
    """Create a bar chart."""
    fig = go.Figure(go.Bar(
        x=df[x], y=df[y],
        marker=dict(
            color=color,
            line=dict(width=0),
            cornerradius=4,
        ),
        opacity=0.85,
    ))
    fig.update_layout(**_base_layout(title, height))
    return fig


def horizontal_bar_chart(labels: list, values: list, title: str = "", colors: list = None, height: int = 300) -> go.Figure:
    """Create a horizontal bar chart."""
    if colors is None:
        colors = [ACCENT_BLUE] * len(labels)
    fig = go.Figure(go.Bar(
        y=labels, x=values,
        orientation="h",
        marker=dict(color=colors, cornerradius=4),
        opacity=0.85,
    ))
    fig.update_layout(**_base_layout(title, height))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def gauge_chart(value: float, title: str = "", max_val: float = 100, height: int = 250) -> go.Figure:
    """Create a gauge/indicator chart."""
    if value >= 85:
        color = ACCENT_GREEN
    elif value >= 70:
        color = ACCENT_YELLOW
    else:
        color = ACCENT_RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(color=TEXT_SECONDARY, size=14)),
        number=dict(font=dict(color=TEXT_COLOR, size=36), suffix="%"),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor=TEXT_SECONDARY),
            bar=dict(color=color, thickness=0.75),
            bgcolor="rgba(255,255,255,0.05)",
            borderwidth=0,
            steps=[
                dict(range=[0, 60], color="rgba(239,68,68,0.15)"),
                dict(range=[60, 85], color="rgba(234,179,8,0.15)"),
                dict(range=[85, 100], color="rgba(34,197,94,0.15)"),
            ],
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=30, r=30, t=40, b=20),
    )
    return fig


def donut_chart(labels: list, values: list, title: str = "", colors: list = None, height: int = 300) -> go.Figure:
    """Create a donut chart."""
    if colors is None:
        colors = COLOR_PALETTE[:len(labels)]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.6,
        marker=dict(colors=colors, line=dict(color=DARK_BG, width=2)),
        textinfo="label+percent",
        textfont=dict(color=TEXT_COLOR, size=11),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=14)) if title else None,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_SECONDARY, size=11)),
        showlegend=True,
    )
    return fig


def treemap_chart(labels: list, parents: list, values: list, title: str = "", height: int = 400) -> go.Figure:
    """Create a treemap chart."""
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=values,
            colorscale=[[0, ACCENT_GREEN], [0.5, ACCENT_YELLOW], [1, ACCENT_RED]],
            line=dict(color=DARK_BG, width=2),
        ),
        textfont=dict(color=TEXT_COLOR),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=14)) if title else None,
    )
    return fig
