"""
Smart Store Page -- Amazon Go-Inspired Autonomous Retail Intelligence
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from dashboard.components.kpi_cards import (
    render_kpi_row, render_page_header, render_section_header, render_footer,
)


def render(store_id: str):
    """Render the Smart Store page."""
    np.random.seed(hash(store_id + "smart") % 2**31)

    render_page_header(
        "Autonomous Retail Intelligence",
        'Smart Store &mdash; "Just Walk Out"',
    )
    st.markdown("""
    <div style="color:#bcc9ca;font-size:0.82rem;margin-top:-20px;margin-bottom:20px;">
        Inspired by Amazon Go &bull; Computer Vision + Weight Sensor Fusion
    </div>
    """, unsafe_allow_html=True)

    # --- KPI Row ---
    render_kpi_row([
        {"label": "Customers In-Store", "value": str(np.random.randint(18, 45)), "icon": "&#x1F6B6;", "chip_text": "Live", "accent": "primary"},
        {"label": "Auto-Restocks Today", "value": str(np.random.randint(20, 60)), "icon": "&#x1F4E6;", "chip_text": "+18% vs avg", "accent": "dim"},
        {"label": "Shrinkage Rate", "value": f"{np.random.uniform(0.8, 1.5):.1f}%", "icon": "&#x1F6E1;", "chip_text": "&#x2193; from 3.2%", "accent": "primary"},
        {"label": "Revenue Impact", "value": f"+${np.random.randint(8, 18)}K", "icon": "&#x1F4B0;", "chip_text": "This Month", "accent": "secondary"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Camera Grid + Customer Journey ---
    col_cameras, col_journey = st.columns([3, 2])

    with col_cameras:
        _render_camera_grid()

    with col_journey:
        _render_customer_journey()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Weight Sensors + Traffic Heatmap ---
    col_sensors, col_heatmap = st.columns(2)

    with col_sensors:
        _render_sensor_dashboard()

    with col_heatmap:
        _render_traffic_heatmap()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Before/After ROI ---
    _render_roi_comparison()

    render_footer()


def _render_camera_grid():
    """Multi-camera surveillance grid."""
    render_section_header("Ceiling Camera Grid", "24 overhead cameras &bull; 4K &bull; 60FPS")

    grid = ""
    cams = [
        ("CAM-01", "Entrance", "optimal"), ("CAM-02", "Produce", "optimal"),
        ("CAM-03", "Aisle 1-2", "low"), ("CAM-04", "Aisle 3-4", "critical"),
        ("CAM-05", "Checkout", "optimal"), ("CAM-06", "Frozen", "optimal"),
    ]
    colors = {"optimal": "#6ee6ee", "low": "#cecb5b", "critical": "#ffb4ab"}

    for cam_id, zone, status in cams:
        c = colors[status]
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        grid += (
            f'<div style="background:#141b2c;border-radius:8px;padding:14px;border:1px solid rgba({r},{g},{b},0.15);display:flex;flex-direction:column;gap:6px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="color:#bcc9ca;font-size:0.7rem;font-weight:600;">{cam_id}</span>'
            f'<span style="width:8px;height:8px;border-radius:50%;background:rgba({r},{g},{b},0.8);"></span>'
            f'</div>'
            f'<div style="height:60px;background:#0b1323;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#69758a;font-size:0.65rem;">&#x1F4F9; {zone}</div>'
            f'<span style="color:{c};font-size:0.6rem;font-weight:500;">{status.upper()}</span>'
            f'</div>'
        )

    st.markdown(f"""
    <div class="panel" style="padding:16px;">
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
            {grid}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_customer_journey():
    """Customer journey funnel."""
    render_section_header("Customer Journey", "Entry-to-Exit Tracking")

    stages = [
        ("Entry Scan", 100, "#6ee6ee"),
        ("Browse & Pick", 92, "#5ed8e0"),
        ("Multi-Pick Events", 68, "#4ecad2"),
        ("Exit & Auto-Charge", 64, "#3db8c0"),
    ]

    funnel_html = ""
    for label, pct, color in stages:
        width = max(40, pct)
        funnel_html += (
            f'<div style="margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
            f'<span style="color:#bcc9ca;font-size:0.75rem;">{label}</span>'
            f'<span style="color:#dbe2f9;font-size:0.75rem;font-weight:700;">{pct}%</span>'
            f'</div>'
            f'<div style="width:{width}%;height:32px;background:linear-gradient(135deg,{color}40,{color}20);border-left:3px solid {color};border-radius:4px;display:flex;align-items:center;padding-left:12px;font-size:0.7rem;font-weight:600;color:{color};">'
            f'{pct} customers'
            f'</div>'
            f'</div>'
        )

    st.markdown(f"""
    <div class="panel" style="padding:18px;">
        {funnel_html}
        <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(61,73,74,0.1);">
            <div style="display:flex;justify-content:space-between;">
                <span style="color:#bcc9ca;font-size:0.72rem;">Avg. Dwell Time</span>
                <span style="color:#6ee6ee;font-weight:700;font-size:0.82rem;">{np.random.randint(8, 18)} min</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:6px;">
                <span style="color:#bcc9ca;font-size:0.72rem;">Auto-Charge Accuracy</span>
                <span style="color:#6ee6ee;font-weight:700;font-size:0.82rem;">99.7%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_sensor_dashboard():
    """Weight sensor network status."""
    render_section_header("Weight Sensor Network", "408 active sensors &bull; 99.2% accuracy")

    zones = [
        ("Zone A: Produce", 68, 67, "#6ee6ee"),
        ("Zone B: Dairy", 52, 50, "#cecb5b"),
        ("Zone C: Beverages", 80, 79, "#6ee6ee"),
        ("Zone D: Frozen", 44, 44, "#6ee6ee"),
        ("Zone E: Snacks", 56, 54, "#ffb4ab"),
    ]

    rows = ""
    for zone, total, active, color in zones:
        pct = round(active / total * 100, 1)
        bar_class = 'healthy' if pct > 90 else 'warning'
        rows += (
            f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;">'
            f'<div style="flex:1;">'
            f'<div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">{zone}</div>'
            f'<div style="color:#69758a;font-size:0.68rem;">{active}/{total} sensors active</div>'
            f'</div>'
            f'<div style="width:100px;">'
            f'<div class="compliance-bar-track">'
            f'<div class="compliance-bar-fill {bar_class}" style="width:{pct}%;"></div>'
            f'</div>'
            f'</div>'
            f'<span style="color:{color};font-size:0.75rem;font-weight:700;width:45px;text-align:right;">{pct}%</span>'
            f'</div>'
        )

    st.markdown(f"""
    <div class="panel" style="padding:18px;">
        {rows}
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(61,73,74,0.1);display:flex;justify-content:space-between;">
            <span style="color:#bcc9ca;font-size:0.72rem;">Avg. Detection Latency</span>
            <span style="color:#6ee6ee;font-weight:700;">187ms</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_traffic_heatmap():
    """Overhead traffic heatmap."""
    render_section_header("In-Store Traffic", "Overhead Heatmap &bull; Live")

    np.random.seed(42)
    grid = np.random.poisson(4, (10, 10)).astype(float)
    grid[2:5, 3:6] += np.random.uniform(6, 12, (3, 3))
    grid[7:9, 1:4] += np.random.uniform(4, 8, (2, 3))

    fig = go.Figure(go.Heatmap(
        z=grid,
        colorscale=[[0, "#0b1323"], [0.4, "rgba(110,230,238,0.2)"], [0.7, "rgba(110,230,238,0.5)"], [1, "#6ee6ee"]],
        showscale=False,
        hovertemplate="Zone %{x},%{y}<br>Visitors: %{z:.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=280, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False), yaxis=dict(visible=False, autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_roi_comparison():
    """Before vs After deployment ROI comparison."""
    render_section_header("Deployment Impact", "Before vs. After Smart Store Technology")

    metrics = [
        ("Stockout Detection Time", "4 hours", "3 minutes", "&#x23F1;"),
        ("Shrinkage Rate", "3.2%", "1.1%", "&#x1F6E1;"),
        ("Labor Cost (per store/mo)", "$45K", "$28K", "&#x1F4B5;"),
        ("Customer Satisfaction", "72%", "94%", "&#x2B50;"),
        ("Inventory Accuracy", "82%", "98.5%", "&#x1F4CA;"),
    ]

    cols = st.columns(len(metrics))
    for col, (label, before, after, icon) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="panel" style="padding:16px;text-align:center;">
                <div style="font-size:1.2rem;margin-bottom:6px;">{icon}</div>
                <div style="color:#bcc9ca;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.05em;font-weight:500;margin-bottom:10px;">{label}</div>
                <div style="color:#ffb4ab;font-size:0.82rem;font-weight:600;text-decoration:line-through;margin-bottom:4px;">{before}</div>
                <div style="color:#6ee6ee;font-size:1.2rem;font-weight:900;">{after}</div>
            </div>
            """, unsafe_allow_html=True)
