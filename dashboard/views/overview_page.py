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
import io

from dashboard.components.kpi_cards import (
    render_kpi_row, render_page_header, render_section_header,
    render_alert_card, render_footer,
)
from dashboard.components.charts import _base_layout, ACCENT_BLUE, TEXT_SECONDARY


# ── Cache KPI values so PDF and display use the same numbers ──────
def _get_kpi_data(store_id: str) -> dict:
    """Generate and cache KPI values for this store."""
    np.random.seed(hash(store_id) % 2**31)
    return {
        "shelf_health": f"{np.random.uniform(90, 97):.1f}",
        "shelf_delta": f"+{np.random.uniform(1, 4):.1f}",
        "oos_units": np.random.randint(8, 25),
        "revenue_recovered": f"{np.random.randint(8, 18):,},480",
        "forecast_accuracy": f"{np.random.uniform(95, 99):.1f}",
    }


def render(store_id: str, store_options: dict):
    """Render the Store Health Dashboard overview."""
    kpi = _get_kpi_data(store_id)

    # --- Page Header (Filter View button REMOVED) ---
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;">
        <div>
            <div class="section-label">Operations Intelligence</div>
            <h1 class="section-title">Store Health Dashboard</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Functional Download Report button ─────────────────────────
    pdf_bytes = _generate_pdf_report(store_id, store_options, kpi)
    st.download_button(
        label="📄 Download Report (PDF)",
        data=pdf_bytes,
        file_name=f"ShelfIQ_Report_{store_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
    )

    # --- Hero KPI Row ---
    render_kpi_row([
        {
            "label": "Shelf Health Score",
            "value": f'{kpi["shelf_health"]}%',
            "icon": "&#x1F6E1;",
            "chip_text": f'{kpi["shelf_delta"]}% vs LW',
            "accent": "primary",
        },
        {
            "label": "Real-time Out-of-Stock",
            "value": f'{kpi["oos_units"]} <span style="font-size:1rem;font-weight:500;color:#bcc9ca;">units</span>',
            "icon": "&#x1F4E6;",
            "chip_text": "High Alert",
            "accent": "error",
        },
        {
            "label": "Revenue Recovered",
            "value": f'₹{kpi["revenue_recovered"]}',
            "icon": "&#x1F4B0;",
            "chip_text": "Estimated",
            "accent": "secondary",
        },
        {
            "label": "Forecast Accuracy",
            "value": f'{kpi["forecast_accuracy"]}%',
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
        _render_critical_alerts(store_id)

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
    """Render the dynamic store floor plan with detection overlay (CHANGE 4)."""
    st.markdown("""
    <div class="panel-low">
        <div class="panel-header">
            <div>
                <h2 style="color: #dbe2f9; font-size: 1.1rem; font-weight: 700; margin:0;">Store Floor Plan — Detection Overlay</h2>
                <p style="color: #bcc9ca; font-size: 0.72rem; margin:2px 0 0 0;">Real-time shelf status from CV pipeline</p>
            </div>
            <div style="display: flex; gap: 14px; align-items: center; font-size: 0.7rem; color: #bcc9ca;">
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:#22c55e;"></span> Healthy</span>
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:#eab308;"></span> Low Stock</span>
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:#ef4444;"></span> Stockout</span>
                <span style="display:flex;align-items:center;gap:5px;"><span style="width:10px;height:10px;border-radius:50%;background:#8b5cf6;"></span> Planogram Violation</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Fetch shelf status data ───────────────────────────────────
    floor_data = _get_floor_plan_data(store_id, num_aisles=5, sections_per_aisle=3)

    # ── Build Plotly scatter floor plan ────────────────────────────
    STATUS_COLORS = {
        "FULL": "#22c55e",
        "LOW": "#eab308",
        "EMPTY": "#ef4444",
        "VIOLATION": "#8b5cf6",
    }
    STATUS_SYMBOLS = {
        "FULL": "square",
        "LOW": "diamond",
        "EMPTY": "x",
        "VIOLATION": "triangle-up",
    }

    fig = go.Figure()

    # Draw aisle background rectangles
    for aisle_idx in range(5):
        y = aisle_idx
        fig.add_shape(
            type="rect",
            x0=-0.4, x1=2.4, y0=y - 0.35, y1=y + 0.35,
            fillcolor="rgba(30,30,60,0.35)",
            line=dict(color="rgba(110,230,238,0.1)", width=1),
            layer="below",
        )

    # Group markers by status for a clean legend
    grouped = {}
    for item in floor_data:
        s = item["status"]
        if s not in grouped:
            grouped[s] = {"x": [], "y": [], "text": [], "hover": []}
        grouped[s]["x"].append(item["section"])
        grouped[s]["y"].append(item["aisle_idx"])
        grouped[s]["text"].append(item["label"])
        grouped[s]["hover"].append(item["hover"])

    for status, pts in grouped.items():
        fig.add_trace(go.Scatter(
            x=pts["x"],
            y=pts["y"],
            mode="markers+text",
            marker=dict(
                color=STATUS_COLORS.get(status, "#bcc9ca"),
                size=28,
                symbol=STATUS_SYMBOLS.get(status, "square"),
                line=dict(width=1.5, color="rgba(255,255,255,0.2)"),
            ),
            text=pts["text"],
            textposition="middle center",
            textfont=dict(size=8, color="white"),
            hovertext=pts["hover"],
            hovertemplate="%{hovertext}<extra></extra>",
            name=status.capitalize(),
            showlegend=False,
        ))

    # Layout
    aisle_labels = [f"Aisle {i+1}" for i in range(5)]
    section_labels = [f"Section {j+1}" for j in range(3)]

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#bcc9ca", family="Inter", size=11),
        height=340,
        margin=dict(l=100, r=30, t=10, b=50),
        xaxis=dict(
            title="Shelf Section",
            ticktext=section_labels,
            tickvals=[0, 1, 2],
            gridcolor="rgba(61,73,74,0.08)",
            range=[-0.6, 2.6],
        ),
        yaxis=dict(
            title="",
            ticktext=aisle_labels,
            tickvals=list(range(5)),
            gridcolor="rgba(61,73,74,0.08)",
            autorange="reversed",
            range=[-0.6, 4.6],
        ),
        hoverlabel=dict(
            bgcolor="rgba(20,27,44,0.95)",
            font_color="#dbe2f9",
            bordercolor="rgba(110,230,238,0.3)",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Bottom stats strip
    full_ct = sum(1 for d in floor_data if d["status"] == "FULL")
    low_ct = sum(1 for d in floor_data if d["status"] == "LOW")
    empty_ct = sum(1 for d in floor_data if d["status"] == "EMPTY")
    viol_ct = sum(1 for d in floor_data if d["status"] == "VIOLATION")

    st.markdown(f"""
        <div style="background:#182030;padding:10px 20px;display:flex;justify-content:space-around;
                    font-size:0.72rem;color:#bcc9ca;border-radius:0 0 12px 12px;">
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#22c55e;"></span>
                Healthy: {full_ct}
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#eab308;"></span>
                Low Stock: {low_ct}
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#ef4444;"></span>
                Stockout: {empty_ct}
            </span>
            <span style="display:flex;align-items:center;gap:6px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#8b5cf6;"></span>
                Violations: {viol_ct}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _get_floor_plan_data(store_id: str, num_aisles: int = 5, sections_per_aisle: int = 3) -> list:
    """
    Get shelf status for the floor plan grid.
    Reads latest detections + compliance from SQLite;
    falls back to seeded synthetic data if database is sparse.
    """
    from data.generators.generate_pos_data import PRODUCT_NAMES

    floor = []

    # ── Try real database data ────────────────────────────────────
    try:
        from database.db_manager import db

        # Get latest detections grouped by aisle + shelf
        detections = db.execute(
            "SELECT aisle_id, shelf_id, stock_level, sku_id "
            "FROM detections WHERE store_id = ? "
            "ORDER BY detected_at DESC LIMIT ?",
            (store_id, num_aisles * sections_per_aisle * 3),
        )

        # Get recent planogram violations
        violations = set()
        try:
            viol_rows = db.execute(
                "SELECT aisle_id, shelf_id FROM alerts "
                "WHERE store_id = ? AND alert_type = 'PLANOGRAM_VIOLATION' "
                "AND acknowledged = 0",
                (store_id,),
            )
            for v in viol_rows:
                violations.add((v.get("aisle_id", ""), v.get("shelf_id", "")))
        except Exception:
            pass

        if detections and len(detections) >= num_aisles:
            # Build a lookup of the latest status per (aisle, shelf) pair
            seen = {}
            for d in detections:
                key = (d.get("aisle_id", ""), d.get("shelf_id", ""))
                if key not in seen:
                    seen[key] = d

            for aisle_idx in range(num_aisles):
                for sec_idx in range(sections_per_aisle):
                    aisle_id = f"A{aisle_idx + 1:02d}"
                    shelf_id = f"SEC-{sec_idx + 1:02d}"
                    key = (aisle_id, shelf_id)

                    det = seen.get(key, None)
                    if det:
                        status = det.get("stock_level", "FULL")
                        sku = det.get("sku_id", "")
                        # Check for planogram violations — overrides status color
                        if key in violations:
                            status = "VIOLATION"
                        sku_idx = int(sku.replace("SKU", "")) - 1 if sku and sku.startswith("SKU") else 0
                        name = PRODUCT_NAMES[sku_idx % len(PRODUCT_NAMES)] if sku else "Unknown"
                    else:
                        status = "FULL"
                        name = "No data"
                        sku = ""

                    fill_pct = {"FULL": "85%", "LOW": "40%", "EMPTY": "0%", "VIOLATION": "—"}[status]
                    floor.append({
                        "aisle_idx": aisle_idx,
                        "section": sec_idx,
                        "status": status,
                        "label": f"A{aisle_idx+1}\nS{sec_idx+1}",
                        "hover": (
                            f"<b>Aisle {aisle_idx+1}, Section {sec_idx+1}</b><br>"
                            f"SKU: {sku} — {name}<br>"
                            f"Status: {status}<br>"
                            f"Fill: {fill_pct}"
                        ),
                    })

            if floor:
                return floor
    except Exception:
        pass

    # ── Fallback: synthetic data ──────────────────────────────────
    np.random.seed(hash(store_id + "floorplan") % 2**31)
    for aisle_idx in range(num_aisles):
        for sec_idx in range(sections_per_aisle):
            rand = np.random.random()
            if rand < 0.55:
                status = "FULL"
            elif rand < 0.75:
                status = "LOW"
            elif rand < 0.88:
                status = "EMPTY"
            else:
                status = "VIOLATION"

            sku_num = np.random.randint(1, 51)
            sku_id = f"SKU{sku_num:03d}"
            name = PRODUCT_NAMES[(sku_num - 1) % len(PRODUCT_NAMES)]
            fill_pct = {"FULL": f"{np.random.randint(75,100)}%", "LOW": f"{np.random.randint(30,55)}%", "EMPTY": f"{np.random.randint(0,15)}%", "VIOLATION": "—"}[status]

            floor.append({
                "aisle_idx": aisle_idx,
                "section": sec_idx,
                "status": status,
                "label": f"A{aisle_idx+1}\nS{sec_idx+1}",
                "hover": (
                    f"<b>Aisle {aisle_idx+1}, Section {sec_idx+1}</b><br>"
                    f"SKU: {sku_id} — {name}<br>"
                    f"Status: {status}<br>"
                    f"Fill: {fill_pct}"
                ),
            })

    return floor


def _render_critical_alerts(store_id: str):
    """Render the top 3 highest priority alerts from AlertManager."""
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

    try:
        from alerts.alert_manager import AlertManager
        mgr = AlertManager()
        live_alerts = mgr.generate_sample_alerts(store_id=store_id, count=3)
    except Exception:
        live_alerts = []

    alerts_list = []
    if not live_alerts:
        # Fallback to static data if manager fails
        alerts_list = [
            render_alert_card(
                "Premium Greek Yogurt - 500g",
                "Shelf E4-2 &bull; 0 units left",
                "Loss Warning", "critical", "2m ago",
                "Est. Daily Loss", "₹1,420",
            ),
            render_alert_card(
                "Energy Drink Multi-pack (x6)",
                "Aisle 09 &bull; Misplaced Item Alert",
                "Compliance", "warning", "14m ago",
                "Sales Risk", "₹890",
            ),
            render_alert_card(
                "Organic Cage-Free Eggs Large",
                "Shelf F1-1 &bull; High Velocity",
                "Out of Stock", "critical", "28m ago",
                "Est. Daily Loss", "₹2,100",
            ),
        ]
    else:
        # Map dynamic alerts to the card renderer
        import datetime
        impact_labels = {5: "Loss Warning", 4: "Loss Warning", 3: "Compliance", 2: "Low Risk", 1: "Low Risk"}
        badge_types = {5: "critical", 4: "critical", 3: "warning", 2: "neutral", 1: "neutral"}
        
        for a in live_alerts[:3]:
            try:
                dt = datetime.datetime.fromisoformat(a.created_at)
                mins_ago = max(1, int((datetime.datetime.now() - dt).total_seconds() / 60))
                time_str = f"{mins_ago}m ago"
            except Exception:
                time_str = "just now"
                
            loss_val = f"₹{a.revenue_impact:,.0f}" if a.revenue_impact else "₹0"
            alerts_list.append(render_alert_card(
                a.message,
                f"{a.sku_id} &bull; {a.aisle_id}/{a.shelf_id}",
                impact_labels.get(a.severity, "Warning"), 
                badge_types.get(a.severity, "warning"), 
                time_str,
                "Est. Loss", 
                loss_val,
            ))

    st.markdown("".join(alerts_list), unsafe_allow_html=True)

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Functional "View All Alerts" button ───────────────────────
    if st.button("🔔 View All 12 Alerts", use_container_width=True, key="view_all_alerts"):
        st.session_state["redirect_to"] = "Alerts"
        st.rerun()


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
                <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin:0;">Real Time Error in Placement</h2>
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


def _pdf_safe(text: str) -> str:
    """Sanitize text for fpdf2 Helvetica (Latin-1 only)."""
    return (
        text
        .replace("\u2014", "-")   # em-dash
        .replace("\u2013", "-")   # en-dash
        .replace("\u2019", "'")   # right single quote
        .replace("\u2018", "'")   # left single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u20b9", "Rs.") # ₹ rupee sign
        .replace("\u2022", "*")   # bullet
        .replace("\u2026", "...")  # ellipsis
    )


def _generate_pdf_report(store_id: str, store_options: dict, kpi: dict) -> bytes:
    """Generate a PDF summary report using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        # Fallback: return a plain-text pseudo-PDF if fpdf2 not installed
        content = (
            f"ShelfIQ Store Health Report\n"
            f"Store: {store_options.get(store_id, store_id)}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Shelf Health Score: {kpi['shelf_health']}%\n"
            f"Out-of-Stock Units: {kpi['oos_units']}\n"
            f"Revenue Recovered: Rs.{kpi['revenue_recovered']}\n"
            f"Forecast Accuracy: {kpi['forecast_accuracy']}%\n"
        )
        return content.encode("utf-8")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(78, 202, 210)
    pdf.cell(0, 15, "ShelfIQ - Store Health Report", new_x="LMARGIN", new_y="NEXT", align="C")

    # Subtitle
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(120, 120, 140)
    store_name = _pdf_safe(store_options.get(store_id, store_id))
    pdf.cell(0, 8, f"Store: {store_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # Divider
    pdf.set_draw_color(78, 202, 210)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)

    # KPI Section
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 30, 60)
    pdf.cell(0, 10, "Key Performance Indicators", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    kpi_items = [
        ("Shelf Health Score", f"{kpi['shelf_health']}%"),
        ("Real-time Out-of-Stock", f"{kpi['oos_units']} units"),
        ("Revenue Recovered", f"Rs.{kpi['revenue_recovered']}"),
        ("Forecast Accuracy", f"{kpi['forecast_accuracy']}%"),
    ]

    pdf.set_font("Helvetica", "", 11)
    for label, value in kpi_items:
        pdf.set_text_color(80, 80, 100)
        pdf.cell(90, 8, _pdf_safe(label))
        pdf.set_text_color(30, 30, 60)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _pdf_safe(value), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)

    pdf.ln(8)

    # Alert Summary
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 30, 60)
    pdf.cell(0, 10, "Critical Alerts Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    alert_items = [
        ("Premium Greek Yogurt - 500g", "Shelf E4-2 - 0 units left", "Rs.1,420 est. daily loss"),
        ("Energy Drink Multi-pack (x6)", "Aisle 09 - Misplaced Item", "Rs.890 sales risk"),
        ("Organic Cage-Free Eggs Large", "Shelf F1-1 - High Velocity", "Rs.2,100 est. daily loss"),
    ]

    pdf.set_font("Helvetica", "", 10)
    for title, detail, impact in alert_items:
        pdf.set_text_color(200, 60, 60)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, _pdf_safe(f"  {title}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(80, 80, 100)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _pdf_safe(f"    {detail} | {impact}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.ln(8)

    # Compliance Section
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 30, 60)
    pdf.cell(0, 10, "Real Time Error in Placement by Aisle", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    aisles_data = [
        ("Aisle 01: Produce", 98),
        ("Aisle 02: Bakery", 94),
        ("Aisle 03: Dairy", 78),
        ("Aisle 04: Meat & Seafood", 91),
        ("Aisle 05: Beverages", 96),
    ]

    for name, pct in aisles_data:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(80, 80, 100)
        pdf.cell(80, 7, _pdf_safe(name))
        if pct >= 85:
            pdf.set_text_color(34, 197, 94)
        else:
            pdf.set_text_color(200, 60, 60)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"{pct}%", new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 170)
    pdf.cell(0, 6, "This report was auto-generated by ShelfIQ Retail Intelligence System.", align="C")

    return bytes(pdf.output())

