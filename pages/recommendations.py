"""
AnalogLab - Idées & Recommandations — Plateforme d'idéation
ENISO · PFE 2025-2026
"""
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
from utils.navbar import render_navbar
from utils.storage_paths import get_recommendations_db_path
from utils.emailjs_notifier import is_emailjs_enabled, send_idea_email

RECOMMENDATIONS_DB_PATH = get_recommendations_db_path()

st.set_page_config(
    page_title="Idées & Recommandations | AnalogLab",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_conn():
    conn = sqlite3.connect(RECOMMENDATIONS_DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Non précisé',
        category TEXT NOT NULL DEFAULT 'Général',
        content TEXT NOT NULL,
        rating INTEGER DEFAULT 5,
        votes INTEGER DEFAULT 0,
        date TEXT NOT NULL DEFAULT ''
    )''')

    c.execute("PRAGMA table_info(recommendations)")
    existing_columns = {row[1] for row in c.fetchall()}
    required_columns = {
        "name": "TEXT NOT NULL DEFAULT ''",
        "role": "TEXT NOT NULL DEFAULT 'Non précisé'",
        "category": "TEXT NOT NULL DEFAULT 'Général'",
        "content": "TEXT NOT NULL DEFAULT ''",
        "rating": "INTEGER DEFAULT 5",
        "votes": "INTEGER DEFAULT 0",
        "date": "TEXT NOT NULL DEFAULT ''",
    }
    for column_name, column_def in required_columns.items():
        if column_name not in existing_columns:
            c.execute(f"ALTER TABLE recommendations ADD COLUMN {column_name} {column_def}")

    conn.commit()
    return conn

conn = get_conn()

# ─── DESIGN SYSTEM ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif !important; background-color:#060A14 !important; }
.stApp {
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,178,0.07) 0%, transparent 55%),
                #060A14 !important;
}

/* UI streamline */
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
footer { display: none !important; }

/* Page hero */
.page-hero { padding:5rem 2rem 3rem; text-align:center; position:relative; }
.hero-glow {
    position:absolute; top:-80px; left:50%; transform:translateX(-50%);
    width:600px; height:350px;
    background:radial-gradient(ellipse, rgba(0,255,178,0.1) 0%, transparent 70%);
}
.hero-rel { position:relative; z-index:1; }
.badge {
    display:inline-flex; align-items:center; gap:8px;
    background:rgba(180,95,255,0.1); border:1px solid rgba(180,95,255,0.3);
    color:#C084FC; padding:6px 20px; border-radius:100px;
    font-size:0.78em; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:1.5rem;
}
.page-title {
    font-size:clamp(2.5rem,6vw,4.5rem); font-weight:900; letter-spacing:-2px;
    background:linear-gradient(135deg,#00FFB2 10%,#00B8FF 60%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    line-height:1.1; margin-bottom:1rem;
}
.page-sub {
    color:#6B7280;
    font-size:1.05em;
    max-width:650px;
    margin:0 auto 2rem;
    line-height:1.7;
    text-align:center !important;
}

/* Stats chips */
.stats-row { display:flex; justify-content:center; gap:2rem; flex-wrap:wrap; margin-bottom:1.5rem; }
.stat-chip {
    background:rgba(0,255,178,0.06); border:1px solid rgba(0,255,178,0.15);
    border-radius:100px; padding:8px 22px; display:flex; align-items:center; gap:8px;
}
.sv { color:#00FFB2; font-weight:900; font-size:1.2em; }
.sl { color:#6B7280; font-size:0.82em; }

/* Idea cards */
.idea-card {
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
    border-radius:18px; padding:1.8rem;
    transition:all 0.35s cubic-bezier(0.175,0.885,0.32,1.275);
    margin-bottom:1rem; position:relative; overflow:hidden;
}
.idea-card:hover {
    transform:translateY(-5px); border-color:rgba(0,255,178,0.15);
}

/* UI overrides buttons */
.stButton > button {
    background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.08) !important;
    color:#9CA3AF !important; border-radius:12px !important; font-weight:600 !important;
    transition:all 0.25s ease !important;
}
.stButton > button:hover {
    background:rgba(0,255,178,0.06) !important; border-color:rgba(0,255,178,0.25) !important;
    color:#00FFB2 !important; transform:translateY(-2px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00FFB2, #00B8FF) !important;
    border: none !important; color: #060A14 !important; font-weight: 800 !important;
}
hr { border-color:rgba(255,255,255,0.05) !important; }

@media (max-width: 900px) {
    .page-hero { padding: 2.6rem 0.8rem 1.6rem; }
    .page-title { font-size: clamp(1.8rem, 10vw, 2.4rem); letter-spacing: -1px; }
    .page-sub { font-size: 0.95em; }
    .stats-row { gap: 0.6rem; }
    .stat-chip { width: 100%; justify-content: center; padding: 8px 12px; }
    .idea-card { padding: 1rem; border-radius: 14px; }
}
</style>
""", unsafe_allow_html=True)

# ─── TOPBAR ──────────────────────────────────────────────────────────────────
render_navbar(active_page="recommendations")

# ─── STATS ───
df_all = pd.read_sql_query("SELECT * FROM recommendations ORDER BY id DESC", conn)
total  = len(df_all)
avg_r  = round(df_all['rating'].mean(), 1) if total > 0 else 0
tot_v  = int(df_all['votes'].sum()) if total > 0 else 0

# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-hero">
    <div class="hero-glow"></div>
    <div class="hero-rel">
        <div class="badge">Idéation Ouverte · ENISO</div>
        <div class="page-title">Partagez vos Idées</div>
        <p class="page-sub" style="text-align:center !important; margin-left:auto; margin-right:auto; max-width:650px; width:100%;">
            Nous construisons <strong>AnalogLab</strong> avec vous. <br>
            Vos suggestions guident nos prochains développements.
        </p>
        <div class="stats-row">
            <div class="stat-chip"><span class="sv">{total}</span><span class="sl">idées</span></div>
            <div class="stat-chip"><span class="sv">{'⭐ '+str(avg_r) if total>0 else '—'}</span><span class="sl">moyenne</span></div>
            <div class="stat-chip"><span class="sv">👍 {tot_v}</span><span class="sl">votes</span></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Formulaire & Liste
col_form, col_list = st.columns([1, 1.6], gap="large")

with col_form:
    st.markdown("### 📝 Soumettre une Idée")
    with st.form("idea_form", clear_on_submit=True):
        name     = st.text_input("Prénom & Nom")
        role     = st.text_input("Métier / École")
        category = st.selectbox("Catégorie", ["💡 Fonctionnalité","🎨 UX / Interface","🔧 Technique / IA","💼 Business","📚 Autre"])
        content  = st.text_area("Votre idée", height=120)
        rating   = st.slider("Note globale", min_value=1, max_value=5, value=5)
        ok = st.form_submit_button("🚀 Soumettre", type="primary", use_container_width=True)
        if ok:
            if name and content:
                try:
                    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                    role_value = role.strip() if role and role.strip() else "Non précisé"
                    c = conn.cursor()
                    c.execute("INSERT INTO recommendations (name,role,category,content,rating,votes,date) VALUES (?,?,?,?,?,?,?)",
                              (name, role_value, category, content, rating, 0, submitted_at))
                    conn.commit()
                except Exception as exc:
                    st.error(f"Impossible d'enregistrer l'idée: {exc}")
                else:
                    if is_emailjs_enabled():
                        try:
                            ok_mail, mail_msg = send_idea_email(
                                name=name.strip(),
                                role=role_value,
                                category=category,
                                content=content.strip(),
                                rating=int(rating),
                                date=submitted_at,
                            )
                            if ok_mail:
                                st.success("📧 Notification idée envoyée (EmailJS).")
                            else:
                                st.warning(f"Idée enregistrée, mais EmailJS a échoué: {mail_msg}")
                        except Exception as exc:
                            st.warning(f"Idée enregistrée, mais EmailJS est mal configuré: {exc}")

                    st.success("🎉 Merci !")
                    st.rerun()
            else:
                st.error("Veuillez renseigner au minimum votre nom et votre idée.")

with col_list:
    st.markdown("### 💬 Suggestions récentes")
    if len(df_all) == 0:
        st.info("Soyez le premier à contribuer !")
    else:
        for _, row in df_all.iterrows():
            st.markdown(f"""
            <div class="idea-card">
                <p style="color:#00FFB2;font-size:0.7em;font-weight:700;margin-bottom:0.4rem;">{row['category']}</p>
                <div style="color:#CBD5E1;font-size:0.95em;line-height:1.6;margin-bottom:1rem;">"{row['content']}"</div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="color:#E2E8F0;font-size:0.8em;font-weight:700;">{row['name']}</div>
                    <div style="color:#6B7280;font-size:0.75em;">👍 {int(row['votes'])} · {row['date']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"👍 Voter", key=f"v_{row['id']}"):
                c = conn.cursor()
                c.execute("UPDATE recommendations SET votes=votes+1 WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

conn.close()
