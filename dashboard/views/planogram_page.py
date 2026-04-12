"""
Shelf Analysis Page -- SKU-Level Detailed Analysis
Matches reference: shelf_detail_sku_analysis
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
import pandas as pd
import io

from dashboard.components.kpi_cards import render_page_header, render_section_header, render_footer


def render(store_id: str):
    """Render the Shelf Analysis / Planogram detail page."""
    np.random.seed(hash(store_id + "shelf") % 2**31)

    # Breadcrumb
    st.markdown("""
    <div style="font-size:0.75rem;color:#6ee6ee;margin-bottom:4px;">
        Aisle 4 &nbsp;&#x203A;&nbsp; Section B &nbsp;&#x203A;&nbsp;
        <span style="color:#bcc9ca;">Shelf Detail</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Page header with functional Export Report button ──────────
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;">
        <div>
            <div class="section-label"></div>
            <h1 class="section-title">Section B: Beverages &amp; Tonics</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Functional buttons row (removed Recalibrate Camera - no longer needed with real feed)

    # --- Main Layout ---
    col_camera, col_alerts = st.columns([5, 3])

    with col_camera:
        _render_camera_feed()
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        _render_planogram_health()

    with col_alerts:
        _render_high_priority_alerts()
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        _render_cv_performance()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SKU Table ---
    _render_sku_table(store_id)

    render_footer()


def _render_camera_feed():
    """Live camera feed with real-time AI detection for planogram compliance."""
    from dashboard.components.camera_feed import render_camera_feed
    render_camera_feed(
        source=0,
        camera_id="CAM_PLANO",
        run_detection=True,
        confidence=0.35,
    )


def _render_planogram_health():
    """Planogram Reference and Health Index cards."""
    match_pct = np.random.randint(94, 99)
    health_delta = round(np.random.uniform(-15, -5), 0)
    health_pct = np.random.randint(75, 90)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="panel" style="padding:18px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Planogram Reference</span>
                <span style="color:#6ee6ee;font-size:0.9rem;">&#x1F4CB;</span>
            </div>
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="width:50px;height:50px;background:#222a3b;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#69758a;">&#x1F5BC;</div>
                <div>
                    <div style="color:#dbe2f9;font-size:1.5rem;font-weight:900;">{match_pct}% Match</div>
                    <div style="color:#69758a;font-size:0.68rem;text-transform:uppercase;">Last Update: 2h ago</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        health_html = (
            '<div class="panel" style="padding:18px;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
            '<span style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Health Index</span>'
            '<span style="color:#cecb5b;font-size:0.9rem;">&#x26A1;</span>'
            '</div>'
            '<div style="display:flex;align-items:center;gap:14px;">'
            f'<div style="width:50px;height:50px;border-radius:50%;border:3px solid #6ee6ee;display:flex;align-items:center;justify-content:center;color:#6ee6ee;font-size:0.8rem;font-weight:700;">{health_pct}%</div>'
            '<div>'
            f'<div style="color:#dbe2f9;font-size:1.5rem;font-weight:900;">{health_delta:.0f}% Low</div>'
            '<div style="color:#69758a;font-size:0.68rem;text-transform:uppercase;">Velocity: High (Aisle 4)</div>'
            '</div>'
            '</div>'
            '</div>'
        )
        st.markdown(health_html, unsafe_allow_html=True)


def _render_high_priority_alerts():
    """High priority alerts sidebar — buttons redirect to Alert Management."""
    st.markdown("""
    <div class="panel">
        <div class="panel-header">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="color:#cecb5b;">&#x1F6A8;</span>
                <span style="color:#dbe2f9;font-size:0.95rem;font-weight:700;">High Priority Alerts</span>
            </div>
        </div>
        <div style="padding:14px;">
            <!-- Alert 1 -->
            <div style="margin-bottom:14px;">
                <div style="display:flex;align-items:flex-start;gap:10px;">
                    <span style="color:#ffb4ab;font-size:1rem;">&#x26A0;</span>
                    <div>
                        <div style="color:#dbe2f9;font-weight:700;font-size:0.88rem;">Stockout: Spark Energy 250ml</div>
                        <div style="color:#bcc9ca;font-size:0.72rem;margin-top:2px;">4 expected facings detected as empty. Lost revenue estimated: ₹240/hr.</div>
                    </div>
                </div>
            </div>
            <div style="border-top:1px solid rgba(61,73,74,0.1);margin:12px 0;"></div>
            <!-- Alert 2 -->
            <div>
                <div style="display:flex;align-items:flex-start;gap:10px;">
                    <span style="color:#cecb5b;font-size:1rem;">&#x2139;</span>
                    <div>
                        <div style="color:#dbe2f9;font-weight:700;font-size:0.88rem;">Price Mismatch: Alpine Water</div>
                        <div style="color:#bcc9ca;font-size:0.72rem;margin-top:2px;">Shelf tag shows ₹99. System lists ₹129. Risk of customer friction.</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Functional buttons that redirect to Alerts page
    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if st.button("🔧 Mark Replenished", key="hp_replenish", use_container_width=True):
            st.session_state["redirect_to"] = "Alerts"
            st.rerun()
    with btn_c2:
        if st.button("🏷️ Verify Price", key="hp_verify", use_container_width=True):
            st.session_state["redirect_to"] = "Alerts"
            st.rerun()


def _render_cv_performance():
    """CV performance metrics panel."""
    latency = np.random.randint(18, 32)
    confidence = round(np.random.uniform(98.5, 99.8), 1)
    lat_w = min(100, latency * 3)

    cv_html = (
        '<div class="panel" style="padding:18px;">'
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">'
        '<span style="color:#6ee6ee;">&#x2699;</span>'
        '<span style="color:#dbe2f9;font-size:0.92rem;font-weight:700;">CV Performance</span>'
        '</div>'
        '<div style="margin-bottom:14px;">'
        '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
        f'<span style="color:#bcc9ca;font-size:0.75rem;">Inference Latency</span>'
        f'<span style="color:#dbe2f9;font-size:0.75rem;font-weight:700;">{latency}ms</span>'
        '</div>'
        '<div class="compliance-bar-track">'
        f'<div class="compliance-bar-fill healthy" style="width:{lat_w}%;"></div>'
        '</div>'
        '</div>'
        '<div style="margin-bottom:14px;">'
        '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
        f'<span style="color:#bcc9ca;font-size:0.75rem;">Model Confidence</span>'
        f'<span style="color:#dbe2f9;font-size:0.75rem;font-weight:700;">{confidence}%</span>'
        '</div>'
        '<div class="compliance-bar-track">'
        f'<div class="compliance-bar-fill healthy" style="width:{confidence}%;"></div>'
        '</div>'
        '</div>'
        '<div style="display:flex;justify-content:space-between;padding-top:8px;border-top:1px solid rgba(61,73,74,0.1);">'
        '<span style="color:#bcc9ca;font-size:0.75rem;">Total SKU Detection Area</span>'
        '<span style="color:#dbe2f9;font-size:0.82rem;font-weight:700;">14.2 sq.m</span>'
        '</div>'
        '</div>'
    )
    st.markdown(cv_html, unsafe_allow_html=True)


def _build_sku_dataframe(store_id: str) -> pd.DataFrame:
    """Build the SKU table data as a DataFrame (used for both display and export)."""
    from data.generators.generate_pos_data import PRODUCT_NAMES

    np.random.seed(hash(store_id) % 2**31)
    rows = []
    for i in range(min(8, len(PRODUCT_NAMES))):
        name = PRODUCT_NAMES[i]
        sku_id = f"SKU-{np.random.randint(1000, 99999):05d}"
        expected = np.random.randint(4, 12)
        detected = expected if i not in [2, 3] else np.random.randint(0, expected)

        # ── FIX: Compute status dynamically from detected vs expected ──
        if detected >= expected:
            status = "IN STOCK"
        elif detected > 0:
            status = "LOW STOCK"
        else:
            status = "OUT OF STOCK"

        # Price accuracy
        if status == "OUT OF STOCK":
            price_acc = "N/A"
        elif i == 3:
            price_acc = "Mismatch"
        else:
            price_acc = "Match"

        # Action
        if status == "OUT OF STOCK":
            action = "REPLENISH"
        elif price_acc == "Mismatch":
            action = "FIX PRICE"
        else:
            action = "—"

        rows.append({
            "product_name": name,
            "sku_id": sku_id,
            "expected": expected,
            "detected": detected,
            "status": status,
            "price_accuracy": price_acc,
            "action": action,
        })

    return pd.DataFrame(rows)


def _render_sku_table(store_id: str):
    """SKU-Level Detailed Analysis table with functional action buttons."""
    render_section_header("SKU-Level Detailed Analysis", "")

    df = _build_sku_dataframe(store_id)

    rows_html = ""
    for i, row in df.iterrows():
        name = row["product_name"]
        sku_id = row["sku_id"]
        expected = row["expected"]
        detected = row["detected"]
        status = row["status"]
        price = row["price_accuracy"]
        action = row["action"]

        check_icon = "&#x2705;" if detected >= expected else "&#x26A0;"
        price_icon = "&#x2705;" if price == "Match" else "&#x1F6D1;" if price == "Mismatch" else "&#x26AB;"

        # Status badge
        if status == "IN STOCK":
            s_class = "in-stock"
        elif status == "LOW STOCK":
            s_class = "low-stock"
        else:
            s_class = "out"

        rows_html += (
            f'<tr style="border-bottom:1px solid rgba(61,73,74,0.08);">'
            f'<td style="padding:12px 14px;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="width:36px;height:36px;background:#222a3b;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#69758a;font-size:0.7rem;">&#x1F4E6;</div>'
            f'<div>'
            f'<div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">{name}</div>'
            f'<div style="color:#69758a;font-size:0.68rem;">{sku_id}</div>'
            f'</div>'
            f'</div>'
            f'</td>'
            f'<td style="padding:12px 14px;text-align:center;">'
            f'<span style="color:#bcc9ca;">{expected}</span> / '
            f'<span style="color:#6ee6ee;font-weight:700;">{detected}</span>'
            f'<span style="margin-left:4px;">{check_icon}</span>'
            f'</td>'
            f'<td style="padding:12px 14px;text-align:center;">'
            f'<span class="sku-status {s_class}">{status}</span>'
            f'</td>'
            f'<td style="padding:12px 14px;text-align:center;">'
            f'{price_icon} {price}'
            f'</td>'
            f'<td style="padding:12px 14px;text-align:center;">'
            f'<span style="color:#69758a;font-size:1.2rem;cursor:pointer;">—</span>'
            f'</td>'
            f'</tr>'
        )

    st.markdown(f"""
    <div class="panel" style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid rgba(61,73,74,0.15);">
                    <th style="text-align:left;padding:12px 14px;color:#bcc9ca;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Product Name / SKU</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Expected vs. Detected</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Stock Status</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Price Accuracy</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Actions</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Functional action buttons below the table ─────────────────
    action_items = df[df["action"].isin(["REPLENISH", "FIX PRICE"])]
    if not action_items.empty:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        act_cols = st.columns(len(action_items) + 2)
        for idx, (_, row) in enumerate(action_items.iterrows()):
            with act_cols[idx]:
                label = f"{'📦' if row['action'] == 'REPLENISH' else '🏷️'} {row['action']}: {row['product_name'][:20]}"
                if st.button(label, key=f"sku_action_{idx}", use_container_width=True):
                    st.session_state["redirect_to"] = "Alerts"
                    st.rerun()
