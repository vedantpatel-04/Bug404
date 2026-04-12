"""
Reusable KPI card and section header components.
Matches the Prama "Intelligent Aperture" design system.
"""
import streamlit as st


def render_kpi_row(metrics: list):
    """
    Render a row of KPI metric cards matching the reference design.
    Each metric: {label, value, chip_text, chip_type, icon, accent}
    accent: "primary" | "error" | "secondary" | "dim"
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        accent = m.get("accent", m.get("color", "primary"))
        chip_text = m.get("chip_text", m.get("delta", ""))
        chip_type = m.get("chip_type", accent)
        icon = m.get("icon", "")

        with col:
            kpi_html = (
                f'<div class="kpi-card accent-{accent}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">'
                f'<div class="kpi-icon-box {accent}">{icon}</div>'
                f'<span class="kpi-chip {chip_type}">{chip_text}</span>'
                f'</div>'
                f'<div class="kpi-label">{m["label"]}</div>'
                f'<div class="kpi-value">{m["value"]}</div>'
                f'</div>'
            )
            st.markdown(kpi_html, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a section header with optional icon prefix."""
    subtitle_html = f'<p style="color:#bcc9ca;font-size:0.8rem;margin-top:2px;">{subtitle}</p>' if subtitle else ""
    icon_html = f'<span>{icon}</span>' if icon else ""
    html = (
        '<div style="margin-bottom:16px;">'
        f'<h2 style="color:#dbe2f9;font-size:1.2rem;font-weight:700;margin:0;display:flex;align-items:center;gap:8px;">'
        f'{icon_html}{title}'
        f'</h2>'
        f'{subtitle_html}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_page_header(section_label: str, title: str, buttons_html: str = ""):
    """Render the page header with section label and action buttons."""
    buttons_block = f'<div style="display:flex;gap:10px;">{buttons_html}</div>' if buttons_html else ""
    html = (
        '<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;">'
        '<div>'
        f'<div class="section-label">{section_label}</div>'
        f'<h1 class="section-title">{title}</h1>'
        '</div>'
        f'{buttons_block}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_status_badge(text: str, badge_type: str = "info"):
    """Render an inline status badge. badge_type: critical | warning | info"""
    return f'<span class="alert-badge {badge_type}">{text}</span>'


def render_alert_card(title: str, subtitle: str, badge_text: str, badge_type: str, 
                      time_ago: str, metric_label: str, metric_value: str):
    """Render a single alert card matching the reference design."""
    severity_class = "severity-critical" if badge_type == "critical" else "severity-warning" if badge_type == "warning" else "severity-info"
    return (
        f'<div class="alert-card {severity_class}" style="margin-bottom:12px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">'
        f'<span class="alert-badge {badge_type}">{badge_text}</span>'
        f'<span style="color:#bcc9ca;font-size:0.65rem;">{time_ago}</span>'
        f'</div>'
        f'<div style="color:#dbe2f9;font-weight:700;font-size:0.9rem;margin-bottom:3px;">{title}</div>'
        f'<div style="color:#bcc9ca;font-size:0.75rem;margin-bottom:10px;">{subtitle}</div>'
        f'<div class="alert-metric-bar">'
        f'<span style="color:#bcc9ca;font-size:0.6rem;text-transform:uppercase;font-weight:600;letter-spacing:0.03em;">{metric_label}</span>'
        f'<span style="color:#dbe2f9;font-size:0.85rem;font-weight:900;">{metric_value}</span>'
        f'</div>'
        f'</div>'
    )


def render_footer():
    """Footer removed — no longer rendered."""
    pass
