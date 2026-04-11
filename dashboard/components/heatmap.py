"""
Heatmap visualizations for stockout frequency and shelf analysis.
"""
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from dashboard.components.charts import DARK_BG, TEXT_COLOR, TEXT_SECONDARY, GRID_COLOR


def stockout_heatmap(title: str = "Stockout Frequency by Aisle & Time of Day", height: int = 400) -> go.Figure:
    """
    Generate a heatmap showing stockout frequency by aisle and hour.
    Uses simulated data for demo.
    """
    np.random.seed(42)
    hours = [f"{h:02d}:00" for h in range(6, 23)]
    aisles = [f"Aisle {i}" for i in range(1, 7)]

    # Simulate stockout patterns: higher during peak hours
    data = np.zeros((len(aisles), len(hours)))
    for i in range(len(aisles)):
        for j, h in enumerate(range(6, 23)):
            base = np.random.uniform(0, 3)
            # Peak hours: 11-14 and 17-20
            if 11 <= h <= 14:
                base += np.random.uniform(2, 5)
            elif 17 <= h <= 20:
                base += np.random.uniform(3, 7)
            # Some aisles are worse
            if i in [0, 2, 4]:
                base *= 1.3
            data[i][j] = round(base, 1)

    fig = go.Figure(go.Heatmap(
        z=data,
        x=hours,
        y=aisles,
        colorscale=[
            [0, "rgba(34, 197, 94, 0.2)"],
            [0.3, "rgba(234, 179, 8, 0.5)"],
            [0.6, "rgba(249, 115, 22, 0.7)"],
            [1, "rgba(239, 68, 68, 0.9)"],
        ],
        colorbar=dict(
            title="Events",
            title_font=dict(color=TEXT_SECONDARY),
            tickfont=dict(color=TEXT_SECONDARY),
        ),
        hovertemplate="<b>%{y}</b> at %{x}<br>Stockouts: %{z}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=16), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=80, r=30, t=50, b=50),
        xaxis=dict(title="Time of Day", gridcolor=GRID_COLOR),
        yaxis=dict(title="", gridcolor=GRID_COLOR),
    )
    return fig


def shelf_health_heatmap(store_id: str = "STORE01", title: str = "Shelf Health Score", height: int = 350) -> go.Figure:
    """
    Generate a heatmap of shelf health scores by aisle and shelf level.
    """
    np.random.seed(hash(store_id) % 2**31)
    aisles = [f"A{i:02d}" for i in range(1, 7)]
    shelf_levels = ["Top", "Upper", "Eye-level", "Lower", "Bottom"]

    data = np.random.uniform(50, 100, (len(shelf_levels), len(aisles)))
    # Eye-level tends to be better stocked
    data[2] = np.clip(data[2] + 15, 0, 100)
    # Bottom shelf often worse
    data[4] = np.clip(data[4] - 10, 0, 100)

    fig = go.Figure(go.Heatmap(
        z=data,
        x=aisles,
        y=shelf_levels,
        colorscale=[
            [0, "rgba(239, 68, 68, 0.9)"],
            [0.4, "rgba(249, 115, 22, 0.7)"],
            [0.7, "rgba(234, 179, 8, 0.5)"],
            [1, "rgba(34, 197, 94, 0.7)"],
        ],
        text=np.round(data, 0).astype(int).astype(str),
        texttemplate="%{text}%",
        textfont=dict(size=12, color="white"),
        colorbar=dict(title="Score %", title_font=dict(color=TEXT_SECONDARY), tickfont=dict(color=TEXT_SECONDARY)),
        hovertemplate="<b>%{y} — %{x}</b><br>Health: %{z:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=16), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=80, r=30, t=50, b=40),
        xaxis=dict(title="Aisle", gridcolor=GRID_COLOR, side="bottom"),
        yaxis=dict(title="Shelf Level", gridcolor=GRID_COLOR, autorange="reversed"),
    )
    return fig


def daily_stockout_heatmap(days: int = 30, title: str = "Daily Stockout Pattern", height: int = 300) -> go.Figure:
    """Calendar-style heatmap of daily stockout counts."""
    np.random.seed(123)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq="D")
    stockouts = np.random.poisson(5, days)
    # Weekends slightly higher
    for i, d in enumerate(dates):
        if d.dayofweek >= 5:
            stockouts[i] = int(stockouts[i] * 1.4)

    weeks = [(d - dates[0]).days // 7 for d in dates]
    dow = [d.dayofweek for d in dates]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    fig = go.Figure(go.Heatmap(
        z=stockouts,
        x=[f"W{w+1}" for w in weeks],
        y=[day_names[d] for d in dow],
        colorscale=[[0, "rgba(34,197,94,0.2)"], [0.5, "rgba(234,179,8,0.5)"], [1, "rgba(239,68,68,0.9)"]],
        hovertemplate="%{y}, %{x}<br>Stockouts: %{z}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=14), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=60, r=20, t=40, b=30),
    )
    return fig
