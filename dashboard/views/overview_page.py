"""
Overview Page -- Store Health Dashboard
Matches the reference: store_health_dashboard
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

from dashboard.components.kpi_cards import (
    render_kpi_row, render_page_header, render_section_header,
    render_alert_card, render_footer,
)
from dashboard.components.charts import _base_layout, ACCENT_BLUE, TEXT_SECONDARY


def render(store_id: str, store_options: dict):
    """Render the Store Health Dashboard overview."""
    np.random.seed(hash(store_id) % 2**31)

    # --- Page Header ---
    render_page_header(
        "Operations Intelligence",
        "Store Health Dashboard",
        '<button class="btn-ghost">&#9776; Filter View</button>'
        '<button class="btn-primary">Download Report</button>',
    )

    # --- Hero KPI Row ---
    render_kpi_row([
        {
            "label": "Shelf Health Score",
            "value": f"{np.random.uniform(90, 97):.1f}%",
            "icon": "&#x1F6E1;",
            "chip_text": f"+{np.random.uniform(1, 4):.1f}% vs LW",
            "accent": "primary",
        },
        {
            "label": "Real-time Out-of-Stock",
            "value": f'{np.random.randint(8, 25)} <span style="font-size:1rem;font-weight:500;color:#bcc9ca;">units</span>',
            "icon": "&#x1F4E6;",
            "chip_text": "High Alert",
            "accent": "error",
        },
        {
            "label": "Revenue Recovered",
            "value": f"${np.random.randint(8, 18):,},480",
            "icon": "&#x1F4B0;",
            "chip_text": "Estimated",
            "accent": "secondary",
        },
        {
            "label": "Forecast Accuracy",
            "value": f"{np.random.uniform(95, 99):.1f}%",
            "icon": "&#x2699;",
            "chip_text": "Model V4.2",
            "accent": "dim",
        },
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Middle: Heatmap + Critical Alerts ---
    col_map, col_alerts = st.columns([2, 1])

    with col_map:
        _render_store_heatmap(store_id)

    with col_alerts:
        _render_critical_alerts()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Bottom Row: Trends + Compliance ---
    col_trends, col_compliance = st.columns(2)

    with col_trends:
        _render_oos_trends()

    with col_compliance:
        _render_compliance_bars()

    # --- Footer ---
    render_footer()


def _render_store_heatmap(store_id: str):
    """Render the store floor heatmap matching the reference."""
    st.markdown("""
    <div class="panel-low">
        <div class="panel-header">
            <div>
                <h2 style="color: #dbe2f9; font-size: 1.1rem; font-weight: 700; margin:0;">Store Floor Heatmap</h2>
                <p style="color: #bcc9ca; font-size: 0.72rem; margin:2px 0 0 0;">High-frequency stockout zones</p>
            </div>
            <div style="display: flex; gap: 14px; align-items: center; font-size: 0.7rem; color: #bcc9ca;">
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:#182030;"></span> Low Risk</span>
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:rgba(110,230,238,0.4);"></span> Medium</span>
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:#6ee6ee;"></span> Critical</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Build heatmap grid
    aisles = ["Produce", "Bakery", "Beverages", "Dairy", "Snacks", "Frozen"]
    sections = [f"S{j+1}" for j in range(8)]
    np.random.seed(42)
    data = np.random.poisson(3, (len(aisles), len(sections))).astype(float)
    # Create hotspots
    data[3, 2:5] += np.random.uniform(6, 12, 3)  # Dairy hotspot
    data[2, 1:3] += np.random.uniform(4, 8, 2)    # Beverages

    fig = go.Figure(go.Heatmap(
        z=data,
        x=sections,
        y=[f"Aisle {i+1:02d}: {a}" for i, a in enumerate(aisles)],
        colorscale=[
            [0, "#182030"],
            [0.3, "rgba(110,230,238,0.15)"],
            [0.6, "rgba(110,230,238,0.4)"],
            [1.0, "#6ee6ee"],
        ],
        hovertemplate="<b>%{y}</b> %{x}<br>Stockout Events: %{z:.0f}<extra></extra>",
        showscale=False,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#060e1e",
        font=dict(color="#bcc9ca", family="Inter", size=11),
        height=320,
        margin=dict(l=130, r=10, t=10, b=30),
        yaxis=dict(autorange="reversed", gridcolor="rgba(61,73,74,0.1)"),
        xaxis=dict(gridcolor="rgba(61,73,74,0.1)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Bottom info strip
    st.markdown("""
        <div style="background:#182030;padding:10px 20px;display:flex;justify-content:space-around;
                    font-size:0.72rem;color:#bcc9ca;border-radius:0 0 12px 12px;">
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#6ee6ee;"></span>
                Highest Velocity: Beverages
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#cecb5b;"></span>
                Delayed Restock: Fresh Produce
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_critical_alerts():
    """Render the critical alerts panel."""
    st.markdown("""
    <div class="panel" style="height: 100%;">
        <div class="panel-header" style="border-bottom: 1px solid rgba(61,73,74,0.1);">
            <div>
                <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin:0;">Critical Alerts</h2>
                <p style="color:#ffb4ab;font-size:0.72rem;font-weight:500;margin:2px 0 0 0;">Top Impact Priority</p>
            </div>
        </div>
        <div style="padding: 14px;">
    """, unsafe_allow_html=True)

    alerts = [
        render_alert_card(
            "Premium Greek Yogurt - 500g",
            "Shelf E4-2 &bull; 0 units left",
            "Loss Warning", "critical", "2m ago",
            "Est. Daily Loss", "$1,420",
        ),
        render_alert_card(
            "Energy Drink Multi-pack (x6)",
            "Aisle 09 &bull; Misplaced Item Alert",
            "Compliance", "warning", "14m ago",
            "Sales Risk", "$890",
        ),
        render_alert_card(
            "Organic Cage-Free Eggs Large",
            "Shelf F1-1 &bull; High Velocity",
            "Out of Stock", "critical", "28m ago",
            "Est. Daily Loss", "$2,100",
        ),
    ]
    st.markdown("".join(alerts), unsafe_allow_html=True)

    st.markdown("""
        </div>
        <div style="padding:12px;text-align:center;border-top:1px solid rgba(61,73,74,0.1);">
            <a style="color:#6ee6ee;font-size:0.82rem;font-weight:700;text-decoration:none;cursor:pointer;">
                View All 12 Alerts
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_oos_trends():
    """Render the Out-of-Stock Trends chart."""
    st.markdown("""
    <div class="panel">
        <div class="panel-header">
            <div>
                <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin:0;">Out-of-Stock Trends</h2>
                <p style="color:#bcc9ca;font-size:0.72rem;margin:2px 0 0 0;">Unit peaks over last 24h</p>
            </div>
            <div style="background:#222a3b;padding:6px 12px;border-radius:8px;font-size:0.72rem;color:#bcc9ca;">
                Last 24 Hours
            </div>
        </div>
    """, unsafe_allow_html=True)

    hours = pd.date_range(end=datetime.now(), periods=24, freq="h")
    values = [12, 10, 8, 6, 5, 4, 5, 8, 14, 18, 22, 28, 25, 20, 18, 22, 30, 35, 28, 22, 18, 14, 10, 8]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=values,
        mode="lines",
        line=dict(color="#6ee6ee", width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(110,230,238,0.08)",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#bcc9ca", size=10),
        height=220, margin=dict(l=30, r=10, t=10, b=30),
        xaxis=dict(gridcolor="rgba(61,73,74,0.1)", tickformat="%H:%M"),
        yaxis=dict(gridcolor="rgba(61,73,74,0.1)"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_compliance_bars():
    """Render the planogram compliance progress bars."""
    avg = np.random.randint(88, 96)
    st.markdown(f"""
    <div class="panel">
        <div class="panel-header">
            <div>
                <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin:0;">Planogram Compliance</h2>
                <p style="color:#bcc9ca;font-size:0.72rem;margin:2px 0 0 0;">Percentage accuracy by aisle</p>
            </div>
            <div class="kpi-chip primary">Avg: {avg}%</div>
        </div>
        <div style="padding: 16px 20px;">
    """, unsafe_allow_html=True)

    aisles_data = [
        ("Aisle 01: Produce", 98),
        ("Aisle 02: Bakery", 94),
        ("Aisle 03: Dairy", 78),
        ("Aisle 04: Meat & Seafood", 91),
        ("Aisle 05: Beverages", 96),
    ]

    bars_html = ""
    for name, pct in aisles_data:
        bar_class = "healthy" if pct >= 85 else "warning"
        text_color = "#dbe2f9" if pct >= 85 else "#ffb4ab"
        bars_html += f"""
        <div style="margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size:0.78rem;font-weight:500;color:{text_color};">{name}</span>
                <span style="font-size:0.78rem;font-weight:700;color:{text_color};">{pct}%</span>
            </div>
            <div class="compliance-bar-track">
                <div class="compliance-bar-fill {bar_class}" style="width:{pct}%;"></div>
            </div>
        </div>
        """

    st.markdown(bars_html + "</div></div>", unsafe_allow_html=True)
