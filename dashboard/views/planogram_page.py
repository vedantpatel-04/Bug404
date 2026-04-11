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

    render_page_header(
        "",
        "Section B: Beverages & Tonics",
        '<button class="btn-ghost">&#x21BB; Recalibrate Camera</button>'
        '<button class="btn-primary">Export Report</button>',
    )

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
    _render_sku_table()

    render_footer()


def _render_camera_feed():
    """Camera feed with detection overlay."""
    det_count = np.random.randint(100, 200)
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #141b2c, #0b1323);
        border-radius: 12px; border: 1px solid rgba(61,73,74,0.15);
        height: 300px; position: relative; overflow: hidden;
    ">
        <!-- Camera info bar -->
        <div style="position:absolute;top:10px;left:10px;display:flex;gap:8px;z-index:2;">
            <span style="background:rgba(110,230,238,0.15);color:#6ee6ee;font-size:0.6rem;padding:4px 10px;border-radius:4px;font-weight:600;">
                &#x1F7E2; LIVE: CAM_4B_NORTH
            </span>
            <span style="background:rgba(20,27,44,0.8);color:#bcc9ca;font-size:0.55rem;padding:4px 8px;border-radius:3px;">
                4K &bull; 60FPS &bull; INFRARED OFF
            </span>
        </div>

        <!-- Detection boxes overlay -->
        <div style="position:absolute;top:80px;left:60px;width:100px;height:70px;border:2px solid #6ee6ee;border-radius:4px;">
            <span style="position:absolute;bottom:-18px;left:0;background:#6ee6ee;color:#00373a;font-size:0.5rem;padding:2px 6px;border-radius:2px;font-weight:700;">SKU_0082-OK</span>
        </div>
        <div style="position:absolute;top:70px;left:180px;width:90px;height:80px;border:2px solid #6ee6ee;border-radius:4px;">
            <span style="position:absolute;bottom:-18px;left:0;background:#6ee6ee;color:#00373a;font-size:0.5rem;padding:2px 6px;border-radius:2px;font-weight:700;">SKU_0082-OK</span>
        </div>
        <div style="position:absolute;top:65px;left:290px;width:85px;height:75px;border:2px solid #ffb4ab;border-radius:4px;">
            <span style="position:absolute;bottom:-18px;left:0;background:#ffb4ab;color:#690005;font-size:0.5rem;padding:2px 6px;border-radius:2px;font-weight:700;">SKU_0082-MISS</span>
        </div>
        <div style="position:absolute;bottom:60px;left:220px;width:110px;height:60px;border:2px dashed #cecb5b;border-radius:4px;">
            <span style="position:absolute;bottom:-18px;left:0;background:#cecb5b;color:#333200;font-size:0.5rem;padding:2px 6px;border-radius:2px;font-weight:700;">PRICE_MISMATCH</span>
        </div>

        <!-- Center placeholder -->
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#69758a;">
            &#x1F4F9; Shelf Camera Feed
        </div>

        <!-- Zoom/capture buttons -->
        <div style="position:absolute;bottom:10px;left:10px;display:flex;gap:6px;">
            <div style="width:30px;height:30px;background:rgba(20,27,44,0.8);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#bcc9ca;font-size:0.8rem;cursor:pointer;">&#x1F50D;</div>
            <div style="width:30px;height:30px;background:rgba(20,27,44,0.8);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#bcc9ca;font-size:0.8rem;cursor:pointer;">&#x1F4F7;</div>
        </div>

        <!-- Detection count -->
        <div style="position:absolute;bottom:10px;right:10px;background:rgba(110,230,238,0.15);color:#6ee6ee;font-size:0.6rem;padding:4px 10px;border-radius:4px;font-weight:600;">
            DETECTIONS: {det_count}
        </div>
    </div>
    """, unsafe_allow_html=True)


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
        st.markdown(f"""
        <div class="panel" style="padding:18px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="color:#bcc9ca;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:500;">Health Index</span>
                <span style="color:#cecb5b;font-size:0.9rem;">&#x26A1;</span>
            </div>
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="
                    width:50px;height:50px;border-radius:50%;
                    border:3px solid #6ee6ee; display:flex;align-items:center;justify-content:center;
                    color:#6ee6ee;font-size:0.8rem;font-weight:700;
                ">{health_pct}%</div>
                <div>
                    <div style="color:#dbe2f9;font-size:1.5rem;font-weight:900;">{health_delta:.0f}% Low</div>
                    <div style="color:#69758a;font-size:0.68rem;text-transform:uppercase;">Velocity: High (Aisle 4)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_high_priority_alerts():
    """High priority alerts sidebar."""
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
                        <div style="color:#bcc9ca;font-size:0.72rem;margin-top:2px;">4 expected facings detected as empty. Lost revenue estimated: $240/hr.</div>
                        <div style="margin-top:8px;">
                            <span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.68rem;padding:4px 12px;border-radius:4px;font-weight:600;cursor:pointer;">MARK AS REPLENISHED</span>
                        </div>
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
                        <div style="color:#bcc9ca;font-size:0.72rem;margin-top:2px;">Shelf tag shows $1.29. System lists $1.49. Risk of customer friction.</div>
                        <div style="margin-top:8px;">
                            <span style="background:rgba(206,203,91,0.12);color:#cecb5b;font-size:0.68rem;padding:4px 12px;border-radius:4px;font-weight:600;cursor:pointer;">VERIFY PRICE TAG</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_cv_performance():
    """CV performance metrics panel."""
    latency = np.random.randint(18, 32)
    confidence = round(np.random.uniform(98.5, 99.8), 1)

    st.markdown(f"""
    <div class="panel" style="padding:18px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
            <span style="color:#6ee6ee;">&#x2699;</span>
            <span style="color:#dbe2f9;font-size:0.92rem;font-weight:700;">CV Performance</span>
        </div>

        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="color:#bcc9ca;font-size:0.75rem;">Inference Latency</span>
                <span style="color:#dbe2f9;font-size:0.75rem;font-weight:700;">{latency}ms</span>
            </div>
            <div class="compliance-bar-track">
                <div class="compliance-bar-fill healthy" style="width:{min(100, latency*3)}%;"></div>
            </div>
        </div>

        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="color:#bcc9ca;font-size:0.75rem;">Model Confidence</span>
                <span style="color:#dbe2f9;font-size:0.75rem;font-weight:700;">{confidence}%</span>
            </div>
            <div class="compliance-bar-track">
                <div class="compliance-bar-fill healthy" style="width:{confidence}%;"></div>
            </div>
        </div>

        <div style="display:flex;justify-content:space-between;padding-top:8px;border-top:1px solid rgba(61,73,74,0.1);">
            <span style="color:#bcc9ca;font-size:0.75rem;">Total SKU Detection Area</span>
            <span style="color:#dbe2f9;font-size:0.82rem;font-weight:700;">14.2 sq.m</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_sku_table():
    """SKU-Level Detailed Analysis table."""
    render_section_header("SKU-Level Detailed Analysis", "")

    from data.generators.generate_pos_data import PRODUCT_NAMES

    np.random.seed(42)
    sku_data = []
    statuses = ["IN STOCK", "IN STOCK", "OUT OF STOCK", "LOW STOCK", "IN STOCK"]
    status_classes = ["in-stock", "in-stock", "out", "low-stock", "in-stock"]
    price_acc = ["Match", "Match", "N/A", "Mismatch", "Match"]
    actions = ["&vellip;", "&vellip;", "REPLENISH", "FIX PRICE", "&vellip;"]

    rows_html = ""
    for i in range(min(8, len(PRODUCT_NAMES))):
        name = PRODUCT_NAMES[i]
        sku_id = f"SKU-{np.random.randint(1000, 99999):05d}"
        expected = np.random.randint(4, 12)
        detected = expected if i not in [2, 3] else np.random.randint(0, expected)
        status_idx = min(i, len(statuses) - 1)
        status = statuses[status_idx]
        s_class = status_classes[status_idx]
        price = price_acc[status_idx]
        action = actions[status_idx]

        check_icon = "&#x2705;" if detected >= expected else "&#x26A0;"
        price_icon = "&#x2705;" if price == "Match" else "&#x1F6D1;" if price == "Mismatch" else "&#x26AB;"

        action_html = f'<span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.65rem;padding:4px 12px;border-radius:4px;font-weight:600;cursor:pointer;">{action}</span>' if action not in ["&vellip;"] else f'<span style="color:#69758a;font-size:1.2rem;cursor:pointer;">{action}</span>'

        rows_html += f"""
        <tr style="border-bottom:1px solid rgba(61,73,74,0.08);">
            <td style="padding:12px 14px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:36px;height:36px;background:#222a3b;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#69758a;font-size:0.7rem;">&#x1F4E6;</div>
                    <div>
                        <div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">{name}</div>
                        <div style="color:#69758a;font-size:0.68rem;">{sku_id}</div>
                    </div>
                </div>
            </td>
            <td style="padding:12px 14px;text-align:center;">
                <span style="color:#bcc9ca;">{expected}</span> /
                <span style="color:#6ee6ee;font-weight:700;">{detected}</span>
                <span style="margin-left:4px;">{check_icon}</span>
            </td>
            <td style="padding:12px 14px;text-align:center;">
                <span class="sku-status {s_class}">{status}</span>
            </td>
            <td style="padding:12px 14px;text-align:center;">
                {price_icon} {price}
            </td>
            <td style="padding:12px 14px;text-align:center;">
                {action_html}
            </td>
        </tr>
        """

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
