"""
ShelfIQ --- Smart Retail Shelf Intelligence Dashboard
Prama "Intelligent Aperture" Design System
Main Streamlit application entry point.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="ShelfIQ | Retail Intelligence",
    page_icon="https://img.icons8.com/fluency/48/barcode-scanner.png",
    layout="wide",
    initial_sidebar_state="expanded",
)



# --- Load Custom CSS ---
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Additional Streamlit overrides ---
st.markdown("""
<style>
    .stApp > header { background: transparent !important; }
    section[data-testid="stSidebar"] { width: 240px !important; min-width: 240px !important; }
    h1, h2, h3, h4, h5, h6 { color: #dbe2f9 !important; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    # Branding
    st.markdown("""
    <div style="padding: 24px 16px 8px 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 34px; height: 34px; border-radius: 8px;
                background: linear-gradient(135deg, #4ecad2, #6ee6ee);
                display: flex; align-items: center; justify-content: center;
                font-size: 1rem; color: #00373a;
            ">&#x1F6D2;</div>
            <div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #e8eaf6;">Intelligence</div>
                <div style="font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.2em; color: #69758a;">Shelf Aperture</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Navigation — read default from session_state so other pages can redirect
    nav_options = [
        "Dashboard",
        "Live Monitor",
        "Shelf Analysis",
        "Shelf Optimizer",
        "Forecast",
        "Alerts",
        "Smart Store",
        "Settings",
    ]
    if "redirect_to" in st.session_state:
        st.session_state["nav_radio"] = st.session_state.pop("redirect_to")

    page = st.radio(
        "nav",
        options=nav_options,
        label_visibility="collapsed",
        key="nav_radio",
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Store selector
    store_options = {
        "STORE01": "Mumbai \u2014 Flagship Store",
        "STORE02": "Ahmedabad \u2014 CG Road",
        "STORE03": "Delhi \u2014 Connaught Place",
    }
    selected_store = st.selectbox(
        "ACTIVE STORE",
        options=list(store_options.keys()),
        format_func=lambda x: store_options[x],
        key="global_store"
    )

    # User profile at bottom
    st.markdown("""
    <div style="
        position: fixed; bottom: 0; left: 0; width: 240px;
        padding: 16px; z-index: 10;
    ">
        <div style="
            background: rgba(20, 27, 44, 0.95);
            border-radius: 12px; padding: 12px 14px;
            display: flex; align-items: center; gap: 10px;
            border: 1px solid rgba(61, 73, 74, 0.1);
        ">
            <div style="
                width: 36px; height: 36px; border-radius: 50%;
                background: linear-gradient(135deg, #4ecad2, #6ee6ee);
                display: flex; align-items: center; justify-content: center;
                color: #00373a; font-weight: 700; font-size: 0.8rem;
            ">AS</div>
            <div>
                <div style="color: #e8eaf6; font-weight: 600; font-size: 0.82rem;">Arjun Sharma</div>
                <div style="color: #69758a; font-size: 0.68rem;">Store Lead</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Page Router ---
if page == "Dashboard":
    from dashboard.views import overview_page
    overview_page.render(selected_store, store_options)

elif page == "Live Monitor":
    from dashboard.views import shelf_monitoring
    shelf_monitoring.render(selected_store)

elif page == "Shelf Analysis":
    from dashboard.views import planogram_page
    planogram_page.render(selected_store)

elif page == "Forecast":
    from dashboard.views import demand_forecast
    demand_forecast.render(selected_store)

elif page == "Alerts":
    from dashboard.views import alerts_page
    alerts_page.render(selected_store)

elif page == "Smart Store":
    from dashboard.views import smart_store
    smart_store.render(selected_store)

elif page == "Shelf Optimizer":
    from dashboard.views import shelf_optimizer_page
    shelf_optimizer_page.render(selected_store)

elif page == "Settings":
    from dashboard.views import analytics_page
    analytics_page.render(selected_store)
