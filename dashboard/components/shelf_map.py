"""
Interactive shelf map component — overlays detection results on a store floor plan grid.
Color-coded sections showing real-time stock status.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from dashboard.components.charts import (
    DARK_BG, TEXT_COLOR, TEXT_SECONDARY, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_RED, ACCENT_BLUE
)


def render_shelf_map(store_id: str = "STORE01", num_aisles: int = 6, shelves_per_aisle: int = 4):
    """
    Render an interactive shelf map as a grid with stock status colors.
    """
    np.random.seed(hash(store_id) % 2**31)

    # Generate stock status data
    statuses = []
    labels = []
    for aisle in range(1, num_aisles + 1):
        for shelf in range(1, shelves_per_aisle + 1):
            rand = np.random.random()
            if rand < 0.60:
                status = "FULL"
            elif rand < 0.82:
                status = "LOW"
            else:
                status = "EMPTY"
            statuses.append(status)
            labels.append(f"A{aisle}-S{shelf}")

    # Create grid for plotly heatmap
    z = []
    text_grid = []
    hover_grid = []
    idx = 0
    for aisle in range(num_aisles):
        row = []
        text_row = []
        hover_row = []
        for shelf in range(shelves_per_aisle):
            status = statuses[idx]
            value = {"FULL": 2, "LOW": 1, "EMPTY": 0}[status]
            row.append(value)
            text_row.append(f"A{aisle+1}\nS{shelf+1}")
            fill_pct = {"FULL": f"{np.random.randint(75, 100)}%", "LOW": f"{np.random.randint(30, 55)}%", "EMPTY": f"{np.random.randint(0, 15)}%"}[status]
            hover_row.append(f"Aisle {aisle+1}, Shelf {shelf+1}<br>Status: {status}<br>Fill: {fill_pct}")
            idx += 1
        z.append(row)
        text_grid.append(text_row)
        hover_grid.append(hover_row)

    fig = go.Figure(go.Heatmap(
        z=z,
        text=text_grid,
        texttemplate="%{text}",
        textfont=dict(color="white", size=11),
        hovertext=hover_grid,
        hovertemplate="%{hovertext}<extra></extra>",
        colorscale=[
            [0, "rgba(239, 68, 68, 0.75)"],      # EMPTY - Red
            [0.5, "rgba(234, 179, 8, 0.75)"],     # LOW - Yellow
            [1, "rgba(34, 197, 94, 0.65)"],        # FULL - Green
        ],
        showscale=False,
        xgap=4,
        ygap=4,
    ))

    fig.update_layout(
        title=dict(text=f"📍 Store Floor Map — {store_id}", font=dict(color=TEXT_COLOR, size=16), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        height=350,
        margin=dict(l=60, r=30, t=50, b=50),
        xaxis=dict(
            title="Shelf Position",
            ticktext=[f"Shelf {i+1}" for i in range(shelves_per_aisle)],
            tickvals=list(range(shelves_per_aisle)),
            gridcolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(
            title="Aisle",
            ticktext=[f"Aisle {i+1}" for i in range(num_aisles)],
            tickvals=list(range(num_aisles)),
            gridcolor="rgba(0,0,0,0)",
            autorange="reversed",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Legend
    st.markdown("""
    <div style="display: flex; gap: 20px; justify-content: center; margin-top: -10px; margin-bottom: 20px;">
        <span style="color: #22c55e;">● Full (>70%)</span>
        <span style="color: #eab308;">● Low (30-70%)</span>
        <span style="color: #ef4444;">● Empty (<30%)</span>
    </div>
    """, unsafe_allow_html=True)

    # Summary stats
    full_count = statuses.count("FULL")
    low_count = statuses.count("LOW")
    empty_count = statuses.count("EMPTY")
    total = len(statuses)

    return {
        "total": total,
        "full": full_count,
        "low": low_count,
        "empty": empty_count,
        "health_pct": round(full_count / total * 100, 1),
    }


def render_aisle_detail(aisle_id: str = "A01", sections: int = 5):
    """Render a detailed aisle view with individual section status."""
    np.random.seed(hash(aisle_id) % 2**31)

    st.markdown(f"#### 🏷️ {aisle_id} — Detailed View")

    cols = st.columns(sections)
    for i, col in enumerate(cols):
        rand = np.random.random()
        if rand < 0.6:
            status, color, emoji = "FULL", "#22c55e", "🟢"
        elif rand < 0.85:
            status, color, emoji = "LOW", "#eab308", "🟡"
        else:
            status, color, emoji = "EMPTY", "#ef4444", "🔴"

        sku = f"SKU{np.random.randint(1, 51):03d}"
        fill = {"FULL": np.random.randint(75, 100), "LOW": np.random.randint(30, 55), "EMPTY": np.random.randint(0, 15)}[status]

        with col:
            st.markdown(f"""
            <div style="
                background: rgba(30,30,60,0.7);
                border: 1px solid {color}40;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                border-top: 3px solid {color};
            ">
                <div style="font-size: 1.5rem;">{emoji}</div>
                <div style="color: {TEXT_COLOR}; font-weight: 600; font-size: 0.85rem;">Sec {i+1}</div>
                <div style="color: {TEXT_SECONDARY}; font-size: 0.75rem;">{sku}</div>
                <div style="color: {color}; font-weight: 700; font-size: 1.1rem;">{fill}%</div>
                <div style="color: {TEXT_SECONDARY}; font-size: 0.7rem;">{status}</div>
            </div>
            """, unsafe_allow_html=True)
