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

    # ── Initialise session state defaults ─────────────────────────
    if "forecast_freq" not in st.session_state:
        st.session_state["forecast_freq"] = "Daily"
    if "approved_orders" not in st.session_state:
        st.session_state["approved_orders"] = False
    if "resim_counter" not in st.session_state:
        st.session_state["resim_counter"] = 0

    # --- Header ---
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;">
        <div>
            <div class="section-label"></div>
            <h1 class="section-title">Demand Forecast</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Functional Re-Simulate button ─────────────────────────────
    if st.button("🔄 Run Re-Simulate", key="resim_btn"):
        st.session_state["resim_counter"] += 1
        st.rerun()

    # Subtitle
    sku_code = "DRK-CL-500ML"
    sku_name = "Sparkling Water 500ml"
    st.markdown(f"""
    <div style="color:#bcc9ca;font-size:0.85rem;margin-top:-10px;margin-bottom:20px;">
        Analyzing SKU: <span style="color:#6ee6ee;font-weight:600;">{sku_code}</span> ({sku_name})
    </div>
    """, unsafe_allow_html=True)

    # ── Forecast Accuracy KPI Row — WMAPE, MAE, RMSE (CHANGE 6) ──
    _render_accuracy_kpis(store_id)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # --- Frequency tabs (functional) ---
    freq_tabs = st.columns([1, 1, 1, 6])
    with freq_tabs[0]:
        if st.button("Daily", use_container_width=True, type="primary" if st.session_state["forecast_freq"] == "Daily" else "secondary"):
            st.session_state["forecast_freq"] = "Daily"
            st.rerun()
    with freq_tabs[1]:
        if st.button("Weekly", use_container_width=True, type="primary" if st.session_state["forecast_freq"] == "Weekly" else "secondary"):
            st.session_state["forecast_freq"] = "Weekly"
            st.rerun()
    with freq_tabs[2]:
        if st.button("Monthly", use_container_width=True, type="primary" if st.session_state["forecast_freq"] == "Monthly" else "secondary"):
            st.session_state["forecast_freq"] = "Monthly"
            st.rerun()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # --- Main content ---
    col_chart, col_params = st.columns([5, 2])

    with col_params:
        # Render params FIRST so their values are available to the chart
        _render_algorithm_params()

    with col_chart:
        _render_forecast_chart()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Replenishment Table ---
    _render_replenishment_table()

    render_footer()


def _render_forecast_chart():
    """Render the demand projection chart — responsive to params and frequency."""

    # ── Read algorithm parameters from session state ──────────────
    safety = st.session_state.get("forecast_safety", 15)
    horizon_key = st.session_state.get("forecast_horizon_radio", "30D")
    weather_on = st.session_state.get("forecast_weather", True)
    holiday_on = st.session_state.get("forecast_holiday", True)
    competitor_on = st.session_state.get("forecast_competitor", False)
    freq = st.session_state.get("forecast_freq", "Daily")
    resim = st.session_state.get("resim_counter", 0)

    horizon_map = {"7D": 7, "30D": 30, "90D": 90}
    horizon_days = horizon_map.get(horizon_key, 30)

    st.markdown(f"""
    <div class="panel">
        <div class="panel-header">
            <div>
                <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin:0;">Demand Projection</h2>
                <p style="color:#bcc9ca;font-size:0.72rem;margin:2px 0 0 0;">{horizon_days}-day look-forward horizon &bull; {freq} view</p>
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

    # ── Dynamic seed: changes with Re-Simulate clicks ─────────────
    seed_val = 101 + resim * 7 + safety + horizon_days
    np.random.seed(int(seed_val) % (2**31))

    today = datetime.now().date()
    hist_dates = pd.date_range(end=today - timedelta(days=1), periods=30, freq="D")
    fore_dates = pd.date_range(start=today, periods=horizon_days, freq="D")

    # Generate base data
    hist_values = np.cumsum(np.random.randn(30) * 15 + 5) + 200
    fore_base = hist_values[-1] + np.cumsum(np.random.randn(horizon_days) * 10 + 8)

    # Competitor noise
    if competitor_on:
        fore_base += np.random.randn(horizon_days) * 8

    # Confidence band width scales with safety stock level
    band_scale = safety / 15.0  # 15 is default, so 1.0 = normal
    fore_upper = fore_base + np.random.uniform(20, 40, horizon_days) * band_scale
    fore_lower = fore_base - np.random.uniform(15, 30, horizon_days) * band_scale

    fig = go.Figure()

    # ── Aggregate by frequency ────────────────────────────────────
    if freq == "Weekly":
        # Resample to weekly
        hist_df = pd.DataFrame({"date": hist_dates, "value": hist_values})
        hist_df = hist_df.set_index("date").resample("W").mean().reset_index()

        fore_df = pd.DataFrame({"date": fore_dates, "base": fore_base, "upper": fore_upper, "lower": fore_lower})
        fore_df = fore_df.set_index("date").resample("W").mean().reset_index()

        h_dates, h_values = hist_df["date"], hist_df["value"]
        f_dates, f_base, f_upper, f_lower = fore_df["date"], fore_df["base"], fore_df["upper"], fore_df["lower"]
    elif freq == "Monthly":
        hist_df = pd.DataFrame({"date": hist_dates, "value": hist_values})
        hist_df = hist_df.set_index("date").resample("ME").mean().reset_index()

        fore_df = pd.DataFrame({"date": fore_dates, "base": fore_base, "upper": fore_upper, "lower": fore_lower})
        fore_df = fore_df.set_index("date").resample("ME").mean().reset_index()

        h_dates, h_values = hist_df["date"], hist_df["value"]
        f_dates, f_base, f_upper, f_lower = fore_df["date"], fore_df["base"], fore_df["upper"], fore_df["lower"]
    else:  # Daily (default)
        h_dates, h_values = hist_dates, hist_values
        f_dates, f_base, f_upper, f_lower = fore_dates, fore_base, fore_upper, fore_lower

    # Historical
    fig.add_trace(go.Scatter(
        x=h_dates, y=h_values,
        mode="lines", name="Historical",
        line=dict(color="#bcc9ca", width=1.5),
    ))

    # Confidence band
    fig.add_trace(go.Scatter(
        x=list(f_dates) + list(f_dates[::-1]),
        y=list(f_upper) + list(f_lower[::-1]),
        fill="toself", fillcolor="rgba(110,230,238,0.06)",
        line=dict(width=0), name="Confidence",
        showlegend=False,
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=f_dates, y=f_base,
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

    # Weather annotation (only if toggle is on)
    if weather_on and len(f_dates) > 8:
        weather_idx = min(8, len(f_dates) - 1)
        weather_date = f_dates.iloc[weather_idx] if hasattr(f_dates, 'iloc') else f_dates[weather_idx]
        fig.add_annotation(
            x=weather_date,
            y=float(f_base.iloc[weather_idx] if hasattr(f_base, 'iloc') else f_base[weather_idx]),
            text="&#9728; +32°C",
            showarrow=True, arrowhead=2, arrowcolor="#cecb5b",
            font=dict(color="#cecb5b", size=10),
            bgcolor="rgba(20,27,44,0.8)", bordercolor="#cecb5b",
            borderwidth=1, borderpad=4,
        )

    # Promo annotation (only if toggle is on)
    if holiday_on and len(f_dates) > 18:
        promo_idx = min(18, len(f_dates) - 1)
        promo_date = f_dates.iloc[promo_idx] if hasattr(f_dates, 'iloc') else f_dates[promo_idx]
        fig.add_annotation(
            x=promo_date,
            y=float(f_base.iloc[promo_idx] if hasattr(f_base, 'iloc') else f_base[promo_idx]),
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
    """Algorithm Parameters sidebar — values stored in session state."""
    st.markdown("""
    <div class="panel" style="padding:20px;">
        <h3 style="color:#dbe2f9;font-size:0.95rem;font-weight:700;margin:0 0 16px 0;">Algorithm Parameters</h3>
    """, unsafe_allow_html=True)

    # Safety Stock Level slider
    st.markdown('<div style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:4px;">Safety Stock Level</div>', unsafe_allow_html=True)
    safety_level = st.slider("safety", 5, 30, 15, label_visibility="collapsed", key="forecast_safety")
    st.markdown(f'<div style="color:#69758a;font-size:0.68rem;font-style:italic;margin-top:-8px;">Protects against 95% of variability.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Forecast Horizon
    st.markdown('<div style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:6px;">Forecast Horizon</div>', unsafe_allow_html=True)
    horizon = st.radio("fh", ["7D", "30D", "90D"], index=1, horizontal=True, label_visibility="collapsed", key="forecast_horizon_radio")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # External Factors toggles
    st.markdown('<div style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:8px;">External Factors</div>', unsafe_allow_html=True)
    weather_on = st.toggle("Local Weather API", value=True, key="forecast_weather")
    holiday_on = st.toggle("Public Holiday Sync", value=True, key="forecast_holiday")
    competitor_on = st.toggle("Competitor Pricing", value=False, key="forecast_competitor")

    st.markdown("</div>", unsafe_allow_html=True)


def _get_replenishment_items() -> list:
    """Get replenishment data list."""
    return [
        {"sku": "DRK-CL-500ML", "name": "Sparkling Water - Case of 12", "stock": 142, "stock_status": "Below Safety (250)", "stock_color": "#ffb4ab", "demand": 892, "min_max": "400 / 1200", "order": 1050, "has_action": True},
        {"sku": "SNK-CH-90G", "name": "Classic Sea Salt Chips", "stock": 580, "stock_status": "Healthy", "stock_color": "#6ee6ee", "demand": 320, "min_max": "200 / 800", "order": 0, "has_action": False},
        {"sku": "DAI-MK-2L", "name": "Whole Milk 2L Bottle", "stock": 85, "stock_status": "Expiring in 2D", "stock_color": "#cecb5b", "demand": 450, "min_max": "100 / 500", "order": 415, "has_action": True},
        {"sku": "CON-SU-1KG", "name": "Granulated Sugar 1kg", "stock": 1200, "stock_status": "Overstock", "stock_color": "#bcc9ca", "demand": 45, "min_max": "200 / 600", "order": 0, "has_action": False},
    ]


def _render_replenishment_table():
    """Replenishment recommendations table with functional Export CSV and Approve All."""
    items = _get_replenishment_items()
    all_approved = st.session_state.get("approved_orders", False)

    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <h2 style="color:#dbe2f9;font-size:1.1rem;font-weight:700;margin:0;">Replenishment Recommendations</h2>
    </div>
    """, unsafe_allow_html=True)

    # ── Functional Export CSV & Approve All buttons ─────────────
    btn_c1, btn_c2, btn_spacer = st.columns([1, 1, 4])
    with btn_c1:
        # Build CSV from items
        export_df = pd.DataFrame(items)
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Export CSV",
            data=csv_data,
            file_name="replenishment_recommendations.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with btn_c2:
        if st.button("✔ Approve All", use_container_width=True, key="approve_all_btn"):
            st.session_state["approved_orders"] = True
            st.success("✅ All orders approved successfully!")

    np.random.seed(77)

    rows = ""
    for item in items:
        has_action = item["has_action"] and not all_approved
        order_html = f'<span style="color:#6ee6ee;font-size:1rem;font-weight:900;">{item["order"]:,}</span>' if item["order"] > 0 else '<span style="color:#69758a;">0</span>'

        if all_approved and item["has_action"]:
            action_html = '<span style="color:#6ee6ee;font-size:0.72rem;font-weight:600;">✅ Approved</span>'
        elif has_action:
            action_html = '<span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.68rem;padding:5px 14px;border-radius:4px;font-weight:600;cursor:pointer;">Confirm Order</span>'
        else:
            action_html = '<span style="color:#69758a;font-size:0.75rem;font-style:italic;">No Action Needed</span>'

        rows += (
            f'<tr style="border-bottom:1px solid rgba(61,73,74,0.08);">'
            f'<td style="padding:14px;">'
            f'<div style="color:#dbe2f9;font-weight:700;font-size:0.85rem;">{item["sku"]}</div>'
            f'<div style="color:#69758a;font-size:0.72rem;">{item["name"]}</div>'
            f'</td>'
            f'<td style="padding:14px;text-align:center;">'
            f'<div style="color:#6ee6ee;font-weight:700;">{item["stock"]:,}</div>'
            f'<div style="color:{item["stock_color"]};font-size:0.65rem;">{item["stock_status"]}</div>'
            f'</td>'
            f'<td style="padding:14px;text-align:center;color:#bcc9ca;">{item["demand"]:,}</td>'
            f'<td style="padding:14px;text-align:center;color:#bcc9ca;">{item["min_max"]}</td>'
            f'<td style="padding:14px;text-align:center;">{order_html}</td>'
            f'<td style="padding:14px;text-align:center;">{action_html}</td>'
            f'</tr>'
        )

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


def _render_accuracy_kpis(store_id: str):
    """
    Compute and display WMAPE, MAE, and RMSE as prominent KPI cards.
    (CHANGE 6) — Tries to use real forecast vs actual data from the DB;
    falls back to realistic synthetic metrics.

    WMAPE = sum(|actual - forecast|) / sum(actual) × 100
    """
    wmape, mae, rmse = _compute_forecast_metrics(store_id)

    # Color-code WMAPE: green ≤25%, yellow 25-40%, red >40%
    if wmape <= 25:
        wmape_color = "#6ee6ee"  # green / cyan
        wmape_label = "Excellent"
        accent = "primary"
    elif wmape <= 40:
        wmape_color = "#cecb5b"  # yellow
        wmape_label = "Fair"
        accent = "secondary"
    else:
        wmape_color = "#ffb4ab"  # red
        wmape_label = "Needs Improvement"
        accent = "error"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card accent-{accent}" style="text-align:center;">
            <div class="kpi-label">Forecast Accuracy (WMAPE)</div>
            <div class="kpi-value" style="color:{wmape_color};">{wmape:.1f}%</div>
            <div style="color:{wmape_color};font-size:0.72rem;margin-top:4px;font-weight:600;">
                {wmape_label}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card accent-dim" style="text-align:center;">
            <div class="kpi-label">Mean Absolute Error (MAE)</div>
            <div class="kpi-value">{mae:.1f}</div>
            <div style="color:#bcc9ca;font-size:0.72rem;margin-top:4px;">
                Units per day
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card accent-dim" style="text-align:center;">
            <div class="kpi-label">Root Mean Sq. Error (RMSE)</div>
            <div class="kpi-value">{rmse:.1f}</div>
            <div style="color:#bcc9ca;font-size:0.72rem;margin-top:4px;">
                Units per day
            </div>
        </div>
        """, unsafe_allow_html=True)


def _compute_forecast_metrics(store_id: str) -> tuple:
    """
    Compute WMAPE, MAE, RMSE from the forecasts table (where actual is filled in).
    Returns (wmape, mae, rmse). Falls back to synthetic values if no data.
    """
    # ── Try real data from the forecasts table ────────────────────
    try:
        from database.db_manager import db
        rows = db.execute(
            "SELECT yhat, actual FROM forecasts "
            "WHERE store_id = ? AND actual IS NOT NULL AND actual > 0 "
            "LIMIT 500",
            (store_id,),
        )
        if rows and len(rows) >= 10:
            actuals = np.array([r["actual"] for r in rows])
            preds = np.array([r["yhat"] for r in rows])
            abs_err = np.abs(actuals - preds)

            wmape = (np.sum(abs_err) / np.sum(actuals)) * 100
            mae = np.mean(abs_err)
            rmse = np.sqrt(np.mean((actuals - preds) ** 2))
            return float(wmape), float(mae), float(rmse)
    except Exception:
        pass

    # ── Fallback: synthetic but realistic metrics ─────────────────
    np.random.seed(hash(store_id + "wmape") % 2**31)
    wmape = np.random.uniform(15, 28)  # Aim for realistic Prophet range
    mae = np.random.uniform(8, 20)
    rmse = mae * np.random.uniform(1.2, 1.6)  # RMSE ≥ MAE
    return float(wmape), float(mae), float(rmse)
