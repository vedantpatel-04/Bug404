"""
Live Monitor Page -- Real-time shelf monitoring with floor plan
Matches reference: live_monitoring_floor_plan
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from dashboard.components.kpi_cards import render_section_header, render_footer


def render(store_id: str):
    """Render the Live Monitoring page."""
    np.random.seed(hash(store_id + "monitor") % 2**31)

    # --- Tab bar ---
    tab1, tab2, tab3 = st.tabs(["Shelf Status", "Planogram Compliance", "Customer Traffic"])

    with tab1:
        _render_shelf_status(store_id)
    with tab2:
        _render_planogram_tab(store_id)
    with tab3:
        _render_traffic_tab(store_id)

    render_footer()


def _render_shelf_status(store_id: str):
    """Main shelf status view with floor plan and aisle detail."""
    # Legend
    st.markdown("""
    <div style="display:flex;gap:20px;margin-bottom:16px;font-size:0.75rem;color:#bcc9ca;">
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:8px;height:8px;border-radius:50%;background:#6ee6ee;"></span> Optimal
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:8px;height:8px;border-radius:50%;background:#cecb5b;"></span> Low Stock
        </span>
        <span style="display:flex;align-items:center;gap:6px;">
            <span style="width:8px;height:8px;border-radius:50%;background:#ffb4ab;"></span> Stockout
        </span>
    </div>
    """, unsafe_allow_html=True)

    col_floor, col_detail = st.columns([3, 2])

    with col_floor:
        _render_floor_plan(store_id)

    with col_detail:
        _render_aisle_detail()


def _render_floor_plan(store_id: str):
    """Render the interactive store floor plan."""
    aisles = [
        {"name": "Aisle 01: Produce", "status": "optimal", "sections": 4},
        {"name": "Aisle 02: Bakery", "status": "optimal", "sections": 3},
        {"name": "Aisle 03: Beverages", "status": "critical", "sections": 5},
        {"name": "Aisle 04: Snacks", "status": "low", "sections": 3},
        {"name": "Frozen Foods", "status": "optimal", "sections": 2},
    ]

    colors = {"optimal": "#6ee6ee", "low": "#cecb5b", "critical": "#ffb4ab"}

    aisle_html = '<div class="panel-low" style="padding:24px;"><div style="display:flex;gap:16px;justify-content:center;align-items:flex-end;min-height:280px;padding:20px;">'
    for a in aisles:
        c = colors[a["status"]]
        height = 60 + a["sections"] * 40
        opacity = "0.25" if a["status"] == "optimal" else "0.5" if a["status"] == "low" else "0.8"
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        border = f"2px dashed {c}" if a["status"] != "optimal" else "1px solid rgba(110,230,238,0.15)"
        glow = "0 0 15px rgba(255,180,171,0.3)" if a["status"] == "critical" else "none"

        aisle_html += (
            f'<div style="width:80px;height:{height}px;'
            f'background:rgba({r},{g},{b},{opacity});'
            f'border:{border};border-radius:6px;'
            f'display:flex;align-items:center;justify-content:center;'
            f'writing-mode:vertical-rl;text-orientation:mixed;'
            f'font-size:0.65rem;font-weight:600;color:{c};'
            f'box-shadow:{glow};cursor:pointer;" title="{a["name"]}">'
            f'{a["name"].upper()}</div>'
        )

    aisle_html += '</div>'
    aisle_html += (
        '<div style="display:flex;gap:8px;justify-content:center;margin-top:16px;">'
        '<div style="width:28px;height:28px;background:#222a3b;border-radius:4px;"></div>'
        '<div style="width:28px;height:28px;background:#222a3b;border-radius:4px;"></div>'
        '<div style="width:28px;height:28px;background:#222a3b;border-radius:4px;"></div>'
        '</div>'
        '<div style="text-align:center;font-size:0.6rem;color:#69758a;margin-top:4px;text-transform:uppercase;letter-spacing:0.1em;">POS Terminals</div>'
        '</div>'
    )

    st.markdown(aisle_html, unsafe_allow_html=True)


def _render_aisle_detail():
    """Render the aisle detail panel with camera feed and detections."""
    np.random.seed(99)
    stock_pct = round(np.random.uniform(60, 85), 1)
    compliance_pct = np.random.randint(82, 96)
    violations = np.random.randint(1, 5)
    det_count = np.random.randint(80, 200)
    delta_pct = round(np.random.uniform(2, 8), 1)

    panel_html = (
        '<div class="panel">'
        '<div class="panel-header">'
        '<div>'
        '<h3 style="color:#dbe2f9;font-size:1.1rem;font-weight:700;margin:0;">Aisle 03: Beverage</h3>'
        '<p style="color:#bcc9ca;font-size:0.72rem;margin:2px 0 0 0;">&#x1F4F7; Camera Unit CAM-09 Active</p>'
        '</div>'
        '<span class="alert-badge critical">Critical Alert</span>'
        '</div>'
        # Camera Feed Placeholder
        '<div style="height:180px;margin:0 16px;background:linear-gradient(135deg,#141b2c 0%,#0b1323 100%);border-radius:8px;border:1px dashed rgba(110,230,238,0.2);display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">'
        '<div style="position:absolute;top:8px;left:8px;display:flex;gap:8px;">'
        '<span style="background:rgba(110,230,238,0.15);color:#6ee6ee;font-size:0.6rem;padding:3px 8px;border-radius:4px;font-weight:600;">&#x1F7E2; LIVE: CAM_09</span>'
        '<span style="background:rgba(30,30,60,0.7);color:#bcc9ca;font-size:0.55rem;padding:3px 6px;border-radius:3px;">4K &bull; 60FPS</span>'
        '</div>'
        '<div style="color:#69758a;font-size:0.8rem;">&#x1F4F9; Live Camera Feed</div>'
        f'<div style="position:absolute;bottom:8px;right:8px;background:rgba(110,230,238,0.15);color:#6ee6ee;font-size:0.6rem;padding:3px 8px;border-radius:4px;font-weight:600;">DETECTIONS: {det_count}</div>'
        '</div>'
        # Stock & Compliance metrics
        '<div style="display:flex;gap:0;margin:16px;">'
        '<div style="flex:1;text-align:center;padding:12px;">'
        '<div style="color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">Stock Level</div>'
        f'<div style="color:#6ee6ee;font-size:1.8rem;font-weight:900;">{stock_pct}%</div>'
        f'<div style="color:#ffb4ab;font-size:0.68rem;">&#x2198; -{delta_pct}% (1h)</div>'
        '</div>'
        '<div style="flex:1;text-align:center;padding:12px;border-left:1px solid rgba(61,73,74,0.1);">'
        '<div style="color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">Compliance</div>'
        f'<div style="color:#dbe2f9;font-size:1.8rem;font-weight:900;">{compliance_pct}%</div>'
        f'<div style="color:#bcc9ca;font-size:0.68rem;">{violations} Violations</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(panel_html, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Real-time detections log
    detections = [
        {"icon": "critical", "emoji": "&#x26A0;", "sku": "Soda 12pk - SKU 8821", "msg": "Level Critical: 0 units remaining on shelf.", "time": "14:22:11"},
        {"icon": "warning", "emoji": "&#x1F4E6;", "sku": "Iced Tea 1L - SKU 4432", "msg": "Planogram mismatch detected (Position 4B).", "time": "14:19:45"},
        {"icon": "success", "emoji": "&#x1F441;", "sku": "Mineral Water - SKU 1109", "msg": "Product replenished. Status: Optimal.", "time": "14:15:02"},
        {"icon": "info", "emoji": "&#x1F464;", "sku": "Customer Engagement", "msg": "High dwell time detected near energy drinks section.", "time": "14:12:30"},
    ]

    det_html = (
        '<div class="panel">'
        '<div class="panel-header" style="border-bottom:1px solid rgba(61,73,74,0.1);">'
        '<div style="color:#dbe2f9;font-size:0.82rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Real-Time Detections</div>'
        '<span style="background:#222a3b;color:#bcc9ca;font-size:0.6rem;padding:3px 8px;border-radius:4px;">LOGS_03</span>'
        '</div>'
    )
    for d in detections:
        det_html += (
            f'<div class="detection-item">'
            f'<div class="detection-icon {d["icon"]}">{d["emoji"]}</div>'
            f'<div style="flex:1;">'
            f'<div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">{d["sku"]}</div>'
            f'<div style="color:#bcc9ca;font-size:0.72rem;">{d["msg"]}</div>'
            f'</div>'
            f'<div style="color:#69758a;font-size:0.68rem;white-space:nowrap;">{d["time"]}</div>'
            f'</div>'
        )

    det_html += (
        '<div style="padding:14px;">'
        '<div style="background:linear-gradient(135deg,#4ecad2,#6ee6ee);color:#00373a;text-align:center;padding:14px;border-radius:10px;font-weight:700;font-size:0.88rem;cursor:pointer;letter-spacing:0.02em;">&#x2705; DEPLOY RESTOCK TASK</div>'
        '</div>'
        '</div>'
    )

    st.markdown(det_html, unsafe_allow_html=True)


def _render_planogram_tab(store_id: str):
    """Planogram compliance view."""
    render_section_header("Planogram Compliance Overview", "Real-time compliance monitoring")

    np.random.seed(hash(store_id + "plano") % 2**31)
    aisles_data = [
        ("Aisle 01: Produce", np.random.randint(92, 99)),
        ("Aisle 02: Bakery", np.random.randint(88, 96)),
        ("Aisle 03: Dairy", np.random.randint(65, 82)),
        ("Aisle 04: Meat & Seafood", np.random.randint(85, 95)),
        ("Aisle 05: Beverages", np.random.randint(90, 98)),
        ("Aisle 06: Snacks", np.random.randint(85, 95)),
    ]

    for name, pct in aisles_data:
        bar_class = "healthy" if pct >= 85 else "warning"
        text_color = "#dbe2f9" if pct >= 85 else "#ffb4ab"
        st.markdown(f"""
        <div style="margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size:0.82rem;font-weight:500;color:{text_color};">{name}</span>
                <span style="font-size:0.82rem;font-weight:700;color:{text_color};">{pct}%</span>
            </div>
            <div class="compliance-bar-track">
                <div class="compliance-bar-fill {bar_class}" style="width:{pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_traffic_tab(store_id: str):
    """Customer traffic heatmap view."""
    render_section_header("Customer Traffic", "Overhead camera tracking")

    import plotly.graph_objects as go
    np.random.seed(hash(store_id + "traffic") % 2**31)

    zones = ["Entrance", "Produce", "Aisles 1-2", "Aisles 3-4", "Checkout"]
    hours = [f"{h}:00" for h in range(8, 22)]
    traffic = np.random.poisson(8, (len(zones), len(hours))).astype(float)
    traffic[0, :] += np.random.uniform(5, 15, len(hours))
    traffic[-1, :] += np.random.uniform(3, 10, len(hours))

    fig = go.Figure(go.Heatmap(
        z=traffic, x=hours, y=zones,
        colorscale=[[0, "#0b1323"], [0.5, "rgba(110,230,238,0.3)"], [1, "#6ee6ee"]],
        showscale=False,
        hovertemplate="<b>%{y}</b> at %{x}<br>Visitors: %{z:.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#bcc9ca", size=10), height=300,
        margin=dict(l=100, r=10, t=10, b=30),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)
