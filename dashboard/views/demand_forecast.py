"""
Demand Forecast Page -- Forecast & Replenishment
Matches reference: forecast_replenishment
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

from dashboard.components.kpi_cards import render_page_header, render_section_header, render_footer
from dashboard.components.charts import _base_layout



def render(store_id: str):
    """Render the Demand Forecast page."""
    np.random.seed(hash(store_id + "forecast") % 2**31)

    # --- Header ---
    render_page_header(
        "",
        "Demand Forecast",
        '<button class="btn-primary">&#x1F504; Run Re-Simulate</button>',
    )

    # Subtitle
    sku_code = "DRK-CL-500ML"
    sku_name = "Sparkling Water 500ml"
    st.markdown(f"""
    <div style="color:#bcc9ca;font-size:0.85rem;margin-top:-20px;margin-bottom:20px;">
        Analyzing SKU: <span style="color:#6ee6ee;font-weight:600;">{sku_code}</span> ({sku_name})
    </div>
    """, unsafe_allow_html=True)

    # --- Frequency tabs ---
    freq_tabs = st.columns([1, 1, 1, 6])
    with freq_tabs[0]:
        daily_btn = st.button("Daily", use_container_width=True)
    with freq_tabs[1]:
        weekly_btn = st.button("Weekly", use_container_width=True)
    with freq_tabs[2]:
        monthly_btn = st.button("Monthly", use_container_width=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # --- Main content ---
    col_chart, col_params = st.columns([5, 2])

    with col_chart:
        _render_forecast_chart()

    with col_params:
        _render_algorithm_params()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Replenishment Table ---
    _render_replenishment_table()

    render_footer()


def _render_forecast_chart():
    """Render the demand projection chart."""
    st.markdown("""
    <div class="panel">
        <div class="panel-header">
            <div>
                <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin:0;">Demand Projection</h2>
                <p style="color:#bcc9ca;font-size:0.72rem;margin:2px 0 0 0;">30-day look-forward horizon</p>
            </div>
            <div style="display:flex;gap:14px;font-size:0.72rem;color:#bcc9ca;">
                <span style="display:flex;align-items:center;gap:5px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#6ee6ee;"></span> Forecast
                </span>
                <span style="display:flex;align-items:center;gap:5px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#bcc9ca;"></span> Historical
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    np.random.seed(101)
    today = datetime.now().date()
    hist_dates = pd.date_range(end=today - timedelta(days=1), periods=30, freq="D")
    fore_dates = pd.date_range(start=today, periods=30, freq="D")

    hist_values = np.cumsum(np.random.randn(30) * 15 + 5) + 200
    fore_base = hist_values[-1] + np.cumsum(np.random.randn(30) * 10 + 8)
    fore_upper = fore_base + np.random.uniform(20, 40, 30)
    fore_lower = fore_base - np.random.uniform(15, 30, 30)

    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=hist_dates, y=hist_values,
        mode="lines", name="Historical",
        line=dict(color="#bcc9ca", width=1.5),
    ))

    # Confidence band
    fig.add_trace(go.Scatter(
        x=list(fore_dates) + list(fore_dates[::-1]),
        y=list(fore_upper) + list(fore_lower[::-1]),
        fill="toself", fillcolor="rgba(110,230,238,0.06)",
        line=dict(width=0), name="Confidence",
        showlegend=False,
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=fore_dates, y=fore_base,
        mode="lines", name="Forecast",
        line=dict(color="#6ee6ee", width=2.5),
    ))

    # TODAY marker
    today_str = today.isoformat()
    fig.add_shape(
        type="line", x0=today_str, x1=today_str,
        y0=0, y1=1, yref="paper",
        line=dict(color="rgba(110,230,238,0.4)", width=2, dash="dash"),
    )
    fig.add_annotation(
        x=today_str, y=0, yref="paper",
        text="TODAY", showarrow=False,
        font=dict(color="#6ee6ee", size=10, family="Inter"),
        yshift=-15,
    )

    # Weather annotation
    weather_date = fore_dates[8].isoformat()
    fig.add_annotation(
        x=weather_date,
        y=float(fore_base[8]),
        text="&#9728; +32°C",
        showarrow=True, arrowhead=2, arrowcolor="#cecb5b",
        font=dict(color="#cecb5b", size=10),
        bgcolor="rgba(20,27,44,0.8)", bordercolor="#cecb5b",
        borderwidth=1, borderpad=4,
    )

    # Promo annotation
    promo_date = fore_dates[18].isoformat()
    fig.add_annotation(
        x=promo_date,
        y=float(fore_base[18]),
        text="&#x1F4B0; BOGO PROMO",
        showarrow=True, arrowhead=2, arrowcolor="#6ee6ee",
        font=dict(color="#00373a", size=9),
        bgcolor="#6ee6ee", borderpad=4,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#bcc9ca", size=10, family="Inter"),
        height=320, margin=dict(l=40, r=10, t=10, b=40),
        xaxis=dict(gridcolor="rgba(61,73,74,0.1)", tickformat="%b %d"),
        yaxis=dict(gridcolor="rgba(61,73,74,0.1)"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_algorithm_params():
    """Algorithm Parameters sidebar."""
    st.markdown("""
    <div class="panel" style="padding:20px;">
        <h3 style="color:#dbe2f9;font-size:0.95rem;font-weight:700;margin:0 0 16px 0;">Algorithm Parameters</h3>
    """, unsafe_allow_html=True)

    # Safety Stock Level slider
    st.markdown('<div style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:4px;">Safety Stock Level</div>', unsafe_allow_html=True)
    safety_level = st.slider("safety", 5, 30, 15, label_visibility="collapsed")
    st.markdown(f'<div style="color:#69758a;font-size:0.68rem;font-style:italic;margin-top:-8px;">Protects against 95% of variability.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Forecast Horizon
    st.markdown('<div style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:6px;">Forecast Horizon</div>', unsafe_allow_html=True)
    horizon = st.radio("fh", ["7D", "30D", "90D"], index=1, horizontal=True, label_visibility="collapsed")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # External Factors toggles
    st.markdown('<div style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:8px;">External Factors</div>', unsafe_allow_html=True)
    weather_on = st.toggle("Local Weather API", value=True)
    holiday_on = st.toggle("Public Holiday Sync", value=True)
    competitor_on = st.toggle("Competitor Pricing", value=False)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_replenishment_table():
    """Replenishment recommendations table."""
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h2 style="color:#dbe2f9;font-size:1.1rem;font-weight:700;margin:0;">Replenishment Recommendations</h2>
        <div style="display:flex;gap:10px;">
            <button class="btn-ghost" style="font-size:0.78rem;padding:8px 16px;">&#x2B07; Export CSV</button>
            <button class="btn-primary" style="font-size:0.78rem;padding:8px 16px;">&#x2714; Approve All</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    np.random.seed(77)
    items = [
        {"sku": "DRK-CL-500ML", "name": "Sparkling Water - Case of 12", "stock": 142, "stock_status": "Below Safety (250)", "stock_color": "#ffb4ab", "demand": 892, "min_max": "400 / 1200", "order": 1050, "has_action": True},
        {"sku": "SNK-CH-90G", "name": "Classic Sea Salt Chips", "stock": 580, "stock_status": "Healthy", "stock_color": "#6ee6ee", "demand": 320, "min_max": "200 / 800", "order": 0, "has_action": False},
        {"sku": "DAI-MK-2L", "name": "Whole Milk 2L Bottle", "stock": 85, "stock_status": "Expiring in 2D", "stock_color": "#cecb5b", "demand": 450, "min_max": "100 / 500", "order": 415, "has_action": True},
        {"sku": "CON-SU-1KG", "name": "Granulated Sugar 1kg", "stock": 1200, "stock_status": "Overstock", "stock_color": "#bcc9ca", "demand": 45, "min_max": "200 / 600", "order": 0, "has_action": False},
    ]

    rows = ""
    for item in items:
        order_html = f'<span style="color:#6ee6ee;font-size:1rem;font-weight:900;">{item["order"]:,}</span>' if item["order"] > 0 else '<span style="color:#69758a;">0</span>'
        action_html = '<span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.68rem;padding:5px 14px;border-radius:4px;font-weight:600;cursor:pointer;">Confirm Order</span>' if item["has_action"] else '<span style="color:#69758a;font-size:0.75rem;font-style:italic;">No Action Needed</span>'

        rows += f"""
        <tr style="border-bottom:1px solid rgba(61,73,74,0.08);">
            <td style="padding:14px;">
                <div style="color:#dbe2f9;font-weight:700;font-size:0.85rem;">{item['sku']}</div>
                <div style="color:#69758a;font-size:0.72rem;">{item['name']}</div>
            </td>
            <td style="padding:14px;text-align:center;">
                <div style="color:#6ee6ee;font-weight:700;">{item['stock']:,}</div>
                <div style="color:{item['stock_color']};font-size:0.65rem;">{item['stock_status']}</div>
            </td>
            <td style="padding:14px;text-align:center;color:#bcc9ca;">{item['demand']:,}</td>
            <td style="padding:14px;text-align:center;color:#bcc9ca;">{item['min_max']}</td>
            <td style="padding:14px;text-align:center;">{order_html}</td>
            <td style="padding:14px;text-align:center;">{action_html}</td>
        </tr>
        """

    st.markdown(f"""
    <div class="panel" style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid rgba(61,73,74,0.15);">
                    <th style="text-align:left;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">SKU & Product Name</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Current Stock</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">7D Demand Pred.</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Min/Max Target</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Suggested Order</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Action</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <div style="padding:12px 16px;display:flex;justify-content:space-between;color:#69758a;font-size:0.72rem;border-top:1px solid rgba(61,73,74,0.1);">
            <span>Showing 4 of 1,248 SKUs</span>
            <span>First &nbsp; Prev &nbsp; <span style="color:#6ee6ee;">1</span> &nbsp; Next &nbsp; Last</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
