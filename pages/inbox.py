"""
AnalogLab - Inbox (Contact + Idées)
"""

import os
import sqlite3

import pandas as pd
import streamlit as st

from utils.navbar import render_navbar
from utils.storage_paths import get_contact_db_path, get_recommendations_db_path

st.set_page_config(
    page_title="Inbox | AnalogLab",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CONTACT_DB_PATH = get_contact_db_path()
RECOMMENDATIONS_DB_PATH = get_recommendations_db_path()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family:'Inter',sans-serif !important; background-color:#060A14 !important; }
    .stApp {
        background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,178,0.07) 0%, transparent 55%), #060A14 !important;
    }
    .block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    footer { display: none !important; }

    .page-hero { padding:4.5rem 2rem 2rem; text-align:center; }
    .hero-title {
        font-size:clamp(2rem,5vw,3.3rem); font-weight:900; letter-spacing:-1.2px;
        background:linear-gradient(135deg,#00FFB2 10%,#00B8FF 60%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        margin-bottom:0.7rem;
    }
    .hero-sub { color:#6B7280; font-size:1em; max-width:900px; margin:0 auto; }
    </style>
    """,
    unsafe_allow_html=True,
)

render_navbar(active_page="inbox")

st.markdown(
    """
    <div class="page-hero">
        <div class="hero-title">Inbox Messages</div>
        <p class="hero-sub">Consultez ici les messages Contact et les idées soumises depuis l'application déployée.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def _load_contact_messages() -> pd.DataFrame:
    if not os.path.exists(CONTACT_DB_PATH):
        return pd.DataFrame(columns=["id", "name", "email", "message", "date"])
    conn = sqlite3.connect(CONTACT_DB_PATH)
    try:
        query = "SELECT id, name, email, message, date FROM messages ORDER BY id DESC"
        return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame(columns=["id", "name", "email", "message", "date"])
    finally:
        conn.close()


def _load_recommendations() -> pd.DataFrame:
    if not os.path.exists(RECOMMENDATIONS_DB_PATH):
        return pd.DataFrame(columns=["id", "name", "role", "category", "content", "rating", "votes", "date"])
    conn = sqlite3.connect(RECOMMENDATIONS_DB_PATH)
    try:
        query = (
            "SELECT id, name, role, category, content, rating, votes, date "
            "FROM recommendations ORDER BY id DESC"
        )
        return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame(columns=["id", "name", "role", "category", "content", "rating", "votes", "date"])
    finally:
        conn.close()


left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("### 📩 Contact")
    df_contact = _load_contact_messages()
    st.caption(f"Total messages: {len(df_contact)}")
    if df_contact.empty:
        st.info("Aucun message contact pour le moment.")
    else:
        st.dataframe(df_contact, use_container_width=True, height=420)

with right:
    st.markdown("### 💡 Idées")
    df_ideas = _load_recommendations()
    st.caption(f"Total idées: {len(df_ideas)}")
    if df_ideas.empty:
        st.info("Aucune idée soumise pour le moment.")
    else:
        st.dataframe(df_ideas, use_container_width=True, height=420)

st.markdown("---")
if st.button("🔄 Rafraîchir", use_container_width=True):
    st.rerun()
