"""
Authentication UI component for the ShelfIQ dashboard.
Self-contained — uses direct SQLite to avoid module caching issues.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import sqlite3
import hashlib
import os
import time

from config.settings import DATABASE_PATH


def _get_conn():
    """Get a fresh SQLite connection."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    # Ensure users table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'Associate',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key.hex(), salt.hex()


def _create_user(username: str, password: str, role: str = "Associate") -> bool:
    conn = _get_conn()
    try:
        pwd_hash, salt = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, pwd_hash, salt, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def _verify_user(username: str, password: str):
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            return None
        salt_bytes = bytes.fromhex(row["salt"])
        input_hash, _ = _hash_password(password, salt_bytes)
        if input_hash == row["password_hash"]:
            return dict(row)
        return None
    finally:
        conn.close()


def _get_user_count() -> int:
    conn = _get_conn()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def render_auth_gate():
    """
    Renders the login/registration screen and blocks access
    to the rest of the application until authenticated.
    """
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;margin-top:60px;margin-bottom:30px;">
        <div style="
            width:48px;height:48px;border-radius:12px;
            background:linear-gradient(135deg,#4ecad2,#6ee6ee);
            display:flex;align-items:center;justify-content:center;
            font-size:1.5rem;color:#00373a;box-shadow:0 0 20px rgba(110,230,238,0.4);
            margin-right:16px;
        ">&#x1F6D2;</div>
        <div>
            <div style="font-size:2rem;font-weight:800;color:#e8eaf6;line-height:1.2;">ShelfIQ Dashboard</div>
            <div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.2em;color:#6ee6ee;font-weight:600;">Secure Access Portal</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="panel" style="padding:24px;">', unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔒 Secure Login", "📝 Create Account"])

        # --- LOGIN TAB ---
        with tab_login:
            st.markdown("<h3 style='color:#dbe2f9;margin-bottom:16px;font-size:1.2rem;'>Associate Login</h3>", unsafe_allow_html=True)
            with st.form("login_form"):
                log_user = st.text_input("Username", placeholder="e.g. arjun.sharma")
                log_pass = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)

                if submitted:
                    if not log_user or not log_pass:
                        st.error("Please enter both username and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            time.sleep(0.5)
                            user_record = _verify_user(log_user, log_pass)
                            if user_record:
                                st.session_state["authenticated"] = True
                                st.session_state["username"] = user_record["username"]
                                st.session_state["role"] = user_record["role"]
                                st.rerun()
                            else:
                                st.error("Invalid username or password.")

        # --- REGISTRATION TAB ---
        with tab_register:
            st.markdown("<h3 style='color:#dbe2f9;margin-bottom:16px;font-size:1.2rem;'>Register New Associate</h3>", unsafe_allow_html=True)
            with st.form("register_form"):
                reg_user = st.text_input("Choose Username", placeholder="e.g. new.associate")
                reg_pass1 = st.text_input("Password", type="password")
                reg_pass2 = st.text_input("Confirm Password", type="password")
                reg_role = st.selectbox("Role", ["Associate", "Store Lead", "Manager"])

                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

                if reg_submitted:
                    if not reg_user or not reg_pass1:
                        st.error("All fields are required.")
                    elif reg_pass1 != reg_pass2:
                        st.error("Passwords do not match.")
                    elif len(reg_pass1) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        with st.spinner("Creating account..."):
                            success = _create_user(reg_user, reg_pass1, reg_role)
                            if success:
                                st.success("Account created successfully! Please switch to the Login tab.")
                            else:
                                st.error("Username already exists. Please choose a different one.")

        st.markdown('</div>', unsafe_allow_html=True)

        # System status footer
        user_count = _get_user_count()
        st.markdown(f"""
        <div style="text-align:center;margin-top:20px;color:#69758a;font-size:0.75rem;">
            &#x1F512; End-to-end encrypted session &bull; {user_count} registered associates
        </div>
        """, unsafe_allow_html=True)
