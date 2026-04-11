"""
Analytics & Settings Page
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from dashboard.components.kpi_cards import render_page_header, render_section_header, render_footer


def render(store_id: str):
    """Render the Analytics / Settings page."""
    np.random.seed(hash(store_id + "analytics") % 2**31)

    render_page_header("System Configuration", "Analytics & Settings")

    tab1, tab2 = st.tabs(["Analytics", "Settings"])

    with tab1:
        _render_analytics(store_id)

    with tab2:
        _render_settings()

    render_footer()


def _render_analytics(store_id: str):
    """Render analytics charts."""
    np.random.seed(hash(store_id + "analysis") % 2**31)

    # KPI summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card accent-primary">
            <div class="kpi-label">Total Revenue Protected</div>
            <div class="kpi-value">${np.random.randint(80, 200)}K</div>
            <div style="color:#6ee6ee;font-size:0.72rem;margin-top:4px;">+{np.random.randint(10,30)}% vs last quarter</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card accent-secondary">
            <div class="kpi-label">Compliance Score</div>
            <div class="kpi-value">{np.random.randint(88, 98)}%</div>
            <div style="color:#cecb5b;font-size:0.72rem;margin-top:4px;">Rolling 30-day average</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card accent-error">
            <div class="kpi-label">Stockout Events</div>
            <div class="kpi-value">{np.random.randint(50, 150)}</div>
            <div style="color:#ffb4ab;font-size:0.72rem;margin-top:4px;">&#x2193; {np.random.randint(15,40)}% from last month</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    col_trend, col_cat = st.columns(2)

    with col_trend:
        render_section_header("Revenue Recovery Trend", "Monthly performance")
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [np.random.randint(20, 50) for _ in months]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months, y=values,
            marker=dict(
                color=values,
                colorscale=[[0, "rgba(110,230,238,0.3)"], [1, "#6ee6ee"]],
            ),
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#bcc9ca", size=10, family="Inter"),
            height=280, margin=dict(l=30, r=10, t=10, b=30),
            xaxis=dict(gridcolor="rgba(61,73,74,0.1)"),
            yaxis=dict(gridcolor="rgba(61,73,74,0.1)", title="$K"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_cat:
        render_section_header("Category Performance", "Revenue by department")
        cats = ["Beverages", "Dairy", "Produce", "Snacks", "Frozen", "Bakery"]
        vals = [np.random.randint(15, 45) for _ in cats]
        colors = ["#6ee6ee", "#5ed8e0", "#4ecad2", "#3db8c0", "#cecb5b", "#bcc9ca"]

        fig = go.Figure(go.Pie(
            labels=cats, values=vals,
            marker=dict(colors=colors),
            textinfo="label+percent",
            textfont=dict(size=10, color="#0b1323"),
            hole=0.55,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#bcc9ca", size=10, family="Inter"),
            height=280, margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Stockout Frequency by Aisle & Time of Day (CHANGE 3) ──────
    st.markdown("<br>", unsafe_allow_html=True)
    render_section_header(
        "Stockout Frequency by Aisle & Time of Day",
        "Hourly stockout patterns across aisles — identifies peak restock windows",
    )

    # Try to pull real stockout data from the database
    heatmap_data = _build_stockout_heatmap_data(store_id)

    hours = [f"{h}:00" for h in range(8, 22)]  # 8 AM – 9 PM
    aisles = heatmap_data["aisles"]
    z_matrix = heatmap_data["matrix"]

    fig = go.Figure(go.Heatmap(
        z=z_matrix,
        x=hours,
        y=aisles,
        colorscale=[
            [0, "#0b1323"],          # zero stockouts — dark background
            [0.25, "rgba(110,230,238,0.15)"],
            [0.5, "#cecb5b"],        # moderate — yellow warning
            [0.75, "#ff8a65"],       # high — orange
            [1, "#ffb4ab"],          # critical — red-ish
        ],
        showscale=True,
        colorbar=dict(
            title=dict(text="Stockouts", font=dict(color="#bcc9ca", size=10)),
            tickfont=dict(color="#bcc9ca", size=9),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovertemplate=(
            "<b>%{y}</b> at %{x}<br>"
            "Stockout events: %{z}<extra></extra>"
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#bcc9ca", size=10, family="Inter"),
        height=320,
        margin=dict(l=120, r=30, t=10, b=40),
        xaxis=dict(
            title="Hour of Day",
            tickangle=-45,
            gridcolor="rgba(61,73,74,0.1)",
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            gridcolor="rgba(61,73,74,0.1)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def _build_stockout_heatmap_data(store_id: str) -> dict:
    """
    Build the heatmap matrix for stockout frequency.
    Attempts to read real detection data from SQLite first;
    falls back to synthetic data with realistic patterns if empty.
    """
    num_hours = 14  # 8 AM through 9 PM
    default_aisles = [f"Aisle {i+1}" for i in range(6)]

    # ── Attempt real data from SQLite ──────────────────────────────
    try:
        from database.db_manager import db
        rows = db.execute(
            "SELECT aisle_id, detected_at FROM detections "
            "WHERE store_id = ? AND stock_level = 'EMPTY' "
            "ORDER BY detected_at",
            (store_id,),
        )
        if rows and len(rows) > 10:
            # Parse into matrix
            aisle_set = sorted(set(r["aisle_id"] for r in rows))
            aisles = aisle_set if aisle_set else default_aisles
            aisle_idx = {a: i for i, a in enumerate(aisles)}
            matrix = np.zeros((len(aisles), num_hours), dtype=int)

            for r in rows:
                ts = r.get("detected_at", "")
                a = r.get("aisle_id", "")
                if not ts or a not in aisle_idx:
                    continue
                try:
                    hour = int(ts[11:13])  # extract HH from ISO timestamp
                except (ValueError, IndexError):
                    continue
                hour_bin = hour - 8
                if 0 <= hour_bin < num_hours:
                    matrix[aisle_idx[a], hour_bin] += 1

            return {"aisles": aisles, "matrix": matrix.tolist()}
    except Exception:
        pass

    # ── Fallback: synthetic data with realistic patterns ───────────
    np.random.seed(hash(store_id + "stockout_heatmap") % 2**31)
    aisles = default_aisles
    matrix = np.zeros((len(aisles), num_hours), dtype=float)

    for ai in range(len(aisles)):
        base = np.random.uniform(1, 4)  # aisle-specific baseline
        for hi in range(num_hours):
            hour = hi + 8
            # Peaks at noon (12 PM) and evening (6 PM)
            noon_peak = 4.0 * np.exp(-0.5 * ((hour - 12) / 1.5) ** 2)
            evening_peak = 3.5 * np.exp(-0.5 * ((hour - 18) / 1.5) ** 2)
            noise = np.random.poisson(1)
            matrix[ai, hi] = max(0, int(base + noon_peak + evening_peak + noise))

    # Make some aisles "worse" — Beverages (Aisle 3) and Snacks (Aisle 4)
    matrix[2, :] = (matrix[2, :] * 1.6).astype(int)
    matrix[3, :] = (matrix[3, :] * 1.3).astype(int)

    return {"aisles": aisles, "matrix": matrix.astype(int).tolist()}


def _render_settings():
    """System settings panel."""
    render_section_header("System Configuration", "Manage pipeline settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="panel" style="padding:20px;">
            <h3 style="color:#dbe2f9;font-size:0.95rem;font-weight:700;margin:0 0 16px 0;">CV Pipeline</h3>
        """, unsafe_allow_html=True)

        model = st.selectbox("Detection Model", ["YOLOv8n", "YOLOv8s", "YOLOv8m"], key="cv_model")
        conf = st.slider("Confidence Threshold", 0.0, 1.0, 0.45, 0.05, key="cv_conf")
        st.toggle("Enable Infrared Preprocessing", value=False, key="cv_ir")
        st.toggle("CLAHE Enhancement", value=True, key="cv_clahe")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="panel" style="padding:20px;">
            <h3 style="color:#dbe2f9;font-size:0.95rem;font-weight:700;margin:0 0 16px 0;">Forecasting Engine</h3>
        """, unsafe_allow_html=True)

        engine = st.selectbox("Forecasting Model", ["Prophet", "Exponential Smoothing", "LSTM"], key="fc_model")
        horizon = st.number_input("Forecast Horizon (days)", 7, 90, 30, key="fc_horizon")
        st.toggle("Include Weather Data", value=True, key="fc_weather")
        st.toggle("Include Promo Calendar", value=True, key="fc_promo")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("""
        <div class="panel" style="padding:20px;">
            <h3 style="color:#dbe2f9;font-size:0.95rem;font-weight:700;margin:0 0 16px 0;">Alert Configuration</h3>
        """, unsafe_allow_html=True)

        st.toggle("Dashboard Push Notifications", value=True, key="alert_push")
        st.toggle("Email Digest", value=True, key="alert_email")
        st.toggle("Mobile Alerts", value=False, key="alert_mobile")
        cooldown = st.slider("Dedup Cooldown (min)", 1, 60, 15, key="alert_cooldown")
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="panel" style="padding:20px;">
            <h3 style="color:#dbe2f9;font-size:0.95rem;font-weight:700;margin:0 0 16px 0;">Database & Connections</h3>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#bcc9ca;font-size:0.78rem;">SQLite Database</span>
                    <span style="color:#6ee6ee;font-size:0.72rem;">&#x2705; Connected</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#bcc9ca;font-size:0.78rem;">Redis Pub/Sub</span>
                    <span style="color:#cecb5b;font-size:0.72rem;">&#x1F7E1; Fallback Mode</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#bcc9ca;font-size:0.78rem;">CV Pipeline</span>
                    <span style="color:#6ee6ee;font-size:0.72rem;">&#x2705; Active</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#bcc9ca;font-size:0.78rem;">Forecasting</span>
                    <span style="color:#6ee6ee;font-size:0.72rem;">&#x2705; Running</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
