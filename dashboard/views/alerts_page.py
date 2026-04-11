"""
Alerts Page -- Alert Inbox + Task Workflow Kanban
Matches reference: alerts_associate_tasks
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import numpy as np
from datetime import datetime

from dashboard.components.kpi_cards import render_footer


def render(store_id: str):
    """Render the Alert Management page."""
    np.random.seed(hash(store_id + "alerts") % 2**31)

    # --- Header KPIs ---
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px;">
        <div>
            <h1 class="section-title">Alert Management</h1>
            <p style="color:#bcc9ca;font-size:0.82rem;margin-top:4px;">
            Operational response for Store &mdash; Mumbai Flagship &mdash; Active Monitoring
            </p>
        </div>
        <div style="display:flex;gap:12px;">
    """, unsafe_allow_html=True)

    avg_resp = round(np.random.uniform(3, 6), 1)
    tasks_resolved = np.random.randint(100, 200)

    st.markdown(f"""
            <div class="kpi-card accent-primary" style="padding:14px 18px;min-width:140px;">
                <div style="color:#bcc9ca;font-size:0.62rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">Avg Response Time</div>
                <div style="color:#6ee6ee;font-size:1.6rem;font-weight:900;">{avg_resp}m</div>
                <div style="color:#bcc9ca;font-size:0.65rem;">&#x2198; 12% from yesterday</div>
            </div>
            <div class="kpi-card accent-dim" style="padding:14px 18px;min-width:140px;">
                <div style="color:#bcc9ca;font-size:0.62rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:500;">Tasks Resolved</div>
                <div style="color:#dbe2f9;font-size:1.6rem;font-weight:900;">{tasks_resolved}</div>
                <div style="color:#6ee6ee;font-size:0.65rem;">&#x2705; 88% completion rate</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Split: Alert Inbox + Task Workflow ---
    col_inbox, col_tasks = st.columns([2, 3])

    with col_inbox:
        _render_alert_inbox()

    with col_tasks:
        _render_task_workflow()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Associate Performance ---
    _render_associate_performance()

    render_footer()


def _render_alert_inbox():
    """Alert inbox with priority sorting and corrective actions (CHANGE 5)."""
    st.markdown("""
    <div class="panel" style="height:100%;">
        <div class="panel-header">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="color:#ffb4ab;">&#x2733;</span>
                <span style="color:#dbe2f9;font-size:0.95rem;font-weight:700;">Alert Inbox</span>
            </div>
            <div style="display:flex;gap:6px;">
                <span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.68rem;padding:4px 10px;border-radius:4px;font-weight:600;">Priority</span>
                <span style="background:#222a3b;color:#bcc9ca;font-size:0.68rem;padding:4px 10px;border-radius:4px;">Time</span>
            </div>
        </div>
        <div style="padding:14px;">
    """, unsafe_allow_html=True)

    # ── Pull alerts with corrective actions from the manager ──────
    try:
        from alerts.alert_manager import AlertManager
        mgr = AlertManager()
        live_alerts = mgr.generate_sample_alerts(count=5)
    except Exception:
        live_alerts = []

    if not live_alerts:
        # Fallback to static data if manager fails
        alerts = [
            {"impact": "HIGH IMPACT &mdash; $1,200", "color": "#ffb4ab", "time": "2m ago",
             "title": "Shelf Stockout: Premium Gin", "detail": "SKU: 004829 &bull; Aisle 4B",
             "corrective": "Restock Premium Gin at Aisle 4B. Suggested reorder qty: 12 units."},
            {"impact": "MED IMPACT &mdash; $450", "color": "#cecb5b", "time": "14m ago",
             "title": "Misplaced Inventory", "detail": "SKU: 119203 &bull; Aisle 12",
             "corrective": "Move product from current position to correct position per planogram layout."},
            {"impact": "LOW IMPACT &mdash; $85", "color": "#bcc9ca", "time": "45m ago",
             "title": "Price Tag Mismatch", "detail": "SKU: 092831 &bull; Aisle 22",
             "corrective": "Update price tag at Aisle 22 from detected price to planogram price."},
        ]
    else:
        # Convert live Alert objects to display-friendly dicts
        impact_labels = {5: "HIGH IMPACT", 4: "HIGH IMPACT", 3: "MED IMPACT", 2: "LOW IMPACT", 1: "LOW IMPACT"}
        impact_colors = {5: "#ffb4ab", 4: "#ffb4ab", 3: "#cecb5b", 2: "#bcc9ca", 1: "#bcc9ca"}
        alerts = []
        for a in live_alerts[:5]:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(a.created_at)
                mins_ago = max(1, int((datetime.now() - dt).total_seconds() / 60))
                time_str = f"{mins_ago}m ago"
            except Exception:
                time_str = "just now"

            alerts.append({
                "impact": f"{impact_labels.get(a.severity, 'ALERT')} &mdash; ${a.revenue_impact:,.0f}",
                "color": impact_colors.get(a.severity, "#bcc9ca"),
                "time": time_str,
                "title": a.message,
                "detail": f"{a.sku_id} &bull; {a.aisle_id}/{a.shelf_id}",
                "corrective": a.corrective_action or a.suggested_action,
            })

    for a in alerts:
        r, g, b = int(a['color'][1:3], 16), int(a['color'][3:5], 16), int(a['color'][5:7], 16)
        card_html = (
            f'<div style="background:#222a3b;border-radius:10px;padding:14px;margin-bottom:12px;border:1px solid rgba({r},{g},{b},0.2);">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
            f'<span style="color:{a["color"]};font-size:0.62rem;font-weight:700;text-transform:uppercase;background:rgba({r},{g},{b},0.1);padding:2px 8px;border-radius:3px;">{a["impact"]}</span>'
            f'<span style="color:#69758a;font-size:0.65rem;">{a["time"]}</span>'
            f'</div>'
            f'<div style="display:flex;gap:12px;align-items:flex-start;">'
            f'<div style="width:60px;height:50px;background:#141b2c;border-radius:6px;flex-shrink:0;display:flex;align-items:center;justify-content:center;color:#69758a;font-size:0.7rem;">&#x1F4F7;</div>'
            f'<div style="flex:1;">'
            f'<div style="color:#dbe2f9;font-weight:700;font-size:0.88rem;">{a["title"]}</div>'
            f'<div style="color:#bcc9ca;font-size:0.72rem;margin-top:2px;">{a["detail"]}</div>'
            # Corrective action line (CHANGE 5)
            f'<div style="color:#6ee6ee;font-size:0.70rem;margin-top:6px;padding:6px 8px;background:rgba(110,230,238,0.06);border-radius:6px;border-left:2px solid #6ee6ee;">'
            f'&#x1F527; <b>Action:</b> {a["corrective"]}'
            f'</div>'
            f'<div style="display:flex;gap:8px;margin-top:10px;">'
            f'<span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.65rem;padding:5px 12px;border-radius:4px;font-weight:600;cursor:pointer;">&#x1F4CB; Assign</span>'
            f'<span style="background:#2d3546;color:#bcc9ca;font-size:0.65rem;padding:5px 12px;border-radius:4px;cursor:pointer;">Details</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


def _render_task_workflow():
    """Kanban-style task workflow."""
    st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="color:#6ee6ee;">&#x1F4CB;</span>
            <span style="color:#dbe2f9;font-size:0.95rem;font-weight:700;">Task Workflow</span>
        </div>
        <span style="color:#bcc9ca;font-size:0.72rem;">Active Associates: 12 Online</span>
    </div>
    """, unsafe_allow_html=True)

    col_todo, col_progress, col_done = st.columns(3)

    with col_todo:
        st.markdown("""
        <div class="panel" style="height:100%;">
            <div style="padding:14px;display:flex;justify-content:space-between;align-items:center;">
                <span style="display:flex;align-items:center;gap:6px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#ffb4ab;"></span>
                    <span style="color:#dbe2f9;font-size:0.82rem;font-weight:700;">TO DO</span>
                </span>
                <span style="color:#69758a;font-size:0.75rem;">8</span>
            </div>
            <div style="padding:0 14px 14px;">
                <div class="task-card todo">
                    <div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">Restock: Organic Milk</div>
                    <div style="color:#bcc9ca;font-size:0.68rem;margin-top:2px;">&#x1F4CD; Dairy Section</div>
                    <div style="display:flex;justify-content:space-between;margin-top:8px;">
                        <span style="background:#2d3546;color:#69758a;font-size:0.6rem;padding:2px 8px;border-radius:3px;">UN</span>
                        <span style="color:#69758a;font-size:0.65rem;">Due: 15m</span>
                    </div>
                </div>
                <div class="task-card todo">
                    <div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">Fix Display: End Cap 5</div>
                    <div style="color:#bcc9ca;font-size:0.68rem;margin-top:2px;">&#x1F4CD; Front Store</div>
                    <div style="display:flex;justify-content:space-between;margin-top:8px;">
                        <span style="background:#2d3546;color:#69758a;font-size:0.6rem;padding:2px 8px;border-radius:3px;">?</span>
                        <span style="color:#ffb4ab;font-size:0.65rem;font-weight:600;">Urgent</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_progress:
        st.markdown("""
        <div class="panel" style="height:100%;">
            <div style="padding:14px;display:flex;justify-content:space-between;align-items:center;">
                <span style="display:flex;align-items:center;gap:6px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#cecb5b;"></span>
                    <span style="color:#dbe2f9;font-size:0.82rem;font-weight:700;">IN PROGRESS</span>
                </span>
                <span style="color:#69758a;font-size:0.75rem;">4</span>
            </div>
            <div style="padding:0 14px 14px;">
                <div class="task-card progress">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">Spill Cleanup</span>
                        <span style="background:rgba(110,230,238,0.12);color:#6ee6ee;font-size:0.6rem;padding:2px 6px;border-radius:3px;">80%</span>
                    </div>
                    <div class="compliance-bar-track" style="margin-top:6px;">
                        <div class="compliance-bar-fill healthy" style="width:80%;"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-top:8px;">
                        <span style="display:flex;align-items:center;gap:4px;">
                            <span style="width:18px;height:18px;border-radius:50%;background:#cecb5b;display:flex;align-items:center;justify-content:center;color:#333200;font-size:0.55rem;font-weight:700;">RD</span>
                            <span style="color:#69758a;font-size:0.65rem;">Rajesh D.</span>
                        </span>
                        <span style="color:#69758a;font-size:0.65rem;">Started 12m ago</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_done:
        st.markdown("""
        <div class="panel" style="height:100%;">
            <div style="padding:14px;display:flex;justify-content:space-between;align-items:center;">
                <span style="display:flex;align-items:center;gap:6px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#6ee6ee;"></span>
                    <span style="color:#dbe2f9;font-size:0.82rem;font-weight:700;">COMPLETED</span>
                </span>
                <span style="color:#69758a;font-size:0.75rem;">24</span>
            </div>
            <div style="padding:0 14px 14px;">
                <div class="task-card complete">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">Restock: Pet Food</span>
                        <span style="color:#6ee6ee;">&#x2705;</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:4px;margin-top:6px;">
                        <span style="width:18px;height:18px;border-radius:50%;background:#6ee6ee;display:flex;align-items:center;justify-content:center;color:#00373a;font-size:0.55rem;font-weight:700;">AS</span>
                        <span style="color:#69758a;font-size:0.65rem;">Verified by system</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Create Manual Task ────────────────────────────────────────
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Initialise manual tasks store
    if "manual_tasks" not in st.session_state:
        st.session_state["manual_tasks"] = []

    with st.expander("\u2795 Create Manual Task", expanded=False):
        with st.form("create_task_form", clear_on_submit=True):
            task_title = st.text_input("Task Title", placeholder="e.g. Restock Organic Milk")
            task_desc = st.text_area("Details", placeholder="Describe the task...")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                assignee = st.selectbox("Assign To", ["Priya M.", "Rajesh D.", "Amit K.", "Kavita L.", "Sneha R.", "Vikram S."])
            with t_col2:
                urgency = st.select_slider("Urgency", options=["Low", "Medium", "High", "Urgent"], value="Medium")
            location = st.text_input("Location", placeholder="e.g. Aisle 3, Dairy Section")
            submitted = st.form_submit_button("\u2705 Create Task", use_container_width=True)
            if submitted and task_title:
                from datetime import datetime
                st.session_state["manual_tasks"].append({
                    "title": task_title,
                    "desc": task_desc,
                    "assignee": assignee,
                    "urgency": urgency,
                    "location": location,
                    "created": datetime.now().strftime("%H:%M"),
                })
                st.success(f"Task '{task_title}' created and assigned to {assignee}!")

    # Show manually created tasks in the TO DO column
    if st.session_state["manual_tasks"]:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div style="color:#dbe2f9;font-size:0.88rem;font-weight:700;margin-bottom:8px;">\U0001f4dd Your Manual Tasks</div>', unsafe_allow_html=True)
        for idx, t in enumerate(st.session_state["manual_tasks"]):
            urgency_colors = {"Low": "#bcc9ca", "Medium": "#cecb5b", "High": "#ff8a65", "Urgent": "#ffb4ab"}
            u_color = urgency_colors.get(t["urgency"], "#bcc9ca")
            st.markdown(f"""
            <div class="task-card todo" style="margin-bottom:8px;">
                <div style="color:#dbe2f9;font-size:0.82rem;font-weight:600;">{t['title']}</div>
                <div style="color:#bcc9ca;font-size:0.68rem;margin-top:2px;">&#x1F4CD; {t['location'] or 'No location'}</div>
                <div style="display:flex;justify-content:space-between;margin-top:8px;">
                    <span style="color:{u_color};font-size:0.65rem;font-weight:600;">{t['urgency']}</span>
                    <span style="color:#69758a;font-size:0.65rem;">Assigned: {t['assignee']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_associate_performance():
    """Associate performance table."""
    st.markdown("""
    <div style="margin-top:20px;">
        <h2 style="color:#dbe2f9;font-size:1.05rem;font-weight:700;margin-bottom:14px;">Associate Performance</h2>
    """, unsafe_allow_html=True)

    np.random.seed(55)
    associates = [
        ("Priya M.", "Active", np.random.randint(10, 25), f"{np.random.uniform(2, 5):.1f}m"),
        ("Rajesh D.", "Active", np.random.randint(10, 25), f"{np.random.uniform(2, 5):.1f}m"),
        ("Amit K.", "Break", np.random.randint(5, 15), f"{np.random.uniform(3, 8):.1f}m"),
        ("Kavita L.", "Active", np.random.randint(15, 30), f"{np.random.uniform(2, 4):.1f}m"),
    ]

    rows = ""
    for name, status, tasks, resp_time in associates:
        status_color = "#6ee6ee" if status == "Active" else "#cecb5b"
        rows += (
            f'<tr style="border-bottom:1px solid rgba(61,73,74,0.08);">'
            f'<td style="padding:12px 14px;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="width:30px;height:30px;border-radius:50%;background:#222a3b;display:flex;align-items:center;justify-content:center;color:#69758a;font-size:0.7rem;">&#x1F464;</div>'
            f'<span style="color:#dbe2f9;font-weight:600;font-size:0.82rem;">{name}</span>'
            f'</div>'
            f'</td>'
            f'<td style="padding:12px 14px;text-align:center;">'
            f'<span style="color:{status_color};font-size:0.72rem;font-weight:500;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{status_color};display:inline-block;margin-right:4px;"></span>'
            f'{status}'
            f'</span>'
            f'</td>'
            f'<td style="padding:12px 14px;text-align:center;color:#dbe2f9;font-weight:600;">{tasks}</td>'
            f'<td style="padding:12px 14px;text-align:center;color:#bcc9ca;">{resp_time}</td>'
            f'</tr>'
        )

    st.markdown(f"""
    <div class="panel" style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="border-bottom:1px solid rgba(61,73,74,0.15);">
                    <th style="text-align:left;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Associate</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Status</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Tasks Done</th>
                    <th style="text-align:center;padding:12px 14px;color:#bcc9ca;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.06em;">Avg Resp. Time</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    </div>
    """, unsafe_allow_html=True)
