"""
AnalogLab - Contact & Support
École Nationale d'Ingénieurs de Sousse (ENISO)
"""
import streamlit as st
import sqlite3
from datetime import datetime
import re
from utils.navbar import render_navbar
from utils.storage_paths import get_contact_db_path
from utils.emailjs_notifier import is_emailjs_enabled, send_contact_email

CONTACT_DB_PATH = get_contact_db_path()

st.set_page_config(
    page_title="Contact | AnalogLab",
    page_icon="📩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def init_db():
    conn = sqlite3.connect(CONTACT_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, message TEXT, date TEXT)''')
    conn.commit()
    return conn

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
    background:rgba(0,255,178,0.1); border:1px solid rgba(0,255,178,0.25);
    color:#00FFB2; padding:6px 20px; border-radius:100px;
    font-size:0.75em; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:1.5rem;
}
.page-title {
    font-size:clamp(2.5rem,6vw,4.5rem); font-weight:900; letter-spacing:-2px;
    background:linear-gradient(135deg,#fff 20%,#9CA3AF 80%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    line-height:1.1; margin-bottom:1rem;
}
.page-sub { color:#6B7280; font-size:1.05em; max-width:650px; margin:0 auto 2rem; line-height:1.7; }

/* Contact info */
.info-box {
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
    border-radius:18px; padding:2rem; height:100%;
}
.info-item { display:flex; gap:1.2rem; margin-bottom:1.5rem; }
.info-icon { font-size:1.4em; }
.info-label { color:#E2E8F0; font-weight:800; font-size:0.95em; margin-bottom:2px; }
.info-val { color:#6B7280; font-size:0.88em; }

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
</style>
""", unsafe_allow_html=True)

# ─── TOPBAR ──────────────────────────────────────────────────────────────────
render_navbar(active_page="contact")

# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
    <div class="hero-glow"></div>
    <div class="hero-rel">
        <div class="badge">Sousse · Tunisie</div>
        <div class="page-title">Restons Connectés</div>
        <p class="page-sub">
            Questions techniques ? Suggestions ? Ou simplement envie de discuter Ingénierie Hardware. 
            Écrivez-nous.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

col_form, col_info = st.columns([1.5, 1], gap="large")

with col_form:
    st.markdown("### 🕊️ Envoyez un message")
    with st.form("contact_form", clear_on_submit=True):
        name = st.text_input("Nom Complet")
        email = st.text_input("Email")
        message = st.text_area("Message", height=150)
        
        submitted = st.form_submit_button("Envoyer →", type="primary", use_container_width=True)
        
        if submitted:
            if not name or not email or not message:
                st.error("Veuillez remplir tous les champs.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Email invalide.")
            else:
                try:
                    sent_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn = init_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO messages (name, email, message, date) VALUES (?, ?, ?, ?)",
                              (name, email, message, sent_at))
                    conn.commit()
                    conn.close()
                except Exception as exc:
                    st.error(f"Impossible d'enregistrer le message: {exc}")
                else:
                    if is_emailjs_enabled():
                        try:
                            ok_mail, mail_msg = send_contact_email(
                                name=name.strip(),
                                email=email.strip(),
                                message=message.strip(),
                                date=sent_at,
                            )
                            if ok_mail:
                                st.success("📧 Notification email envoyée (EmailJS).")
                            else:
                                st.warning(f"Message enregistré, mais EmailJS a échoué: {mail_msg}")
                        except Exception as exc:
                            st.warning(f"Message enregistré, mais EmailJS est mal configuré: {exc}")

                    st.success("🎉 Message envoyé ! On vous répond sous 24h.")

with col_info:
    st.markdown("### 🏛️ Informations")
    st.markdown("""
    <div class="info-box">
        <div class="info-item">
            <span class="info-icon">📍</span>
            <div>
                <div class="info-label">Bureau Sousse</div>
                <div class="info-val">ENISO, Technopole de Sousse<br>4023, Tunisie</div>
            </div>
        </div>
        <div class="info-item">
            <span class="info-icon">📧</span>
            <div>
                <div class="info-label">Email</div>
                <div class="info-val">pfe-analoglab@eniso.u-sousse.tn</div>
            </div>
        </div>
        <div class="info-item">
            <span class="info-icon">🛠️</span>
            <div>
                <div class="info-label">GitHub</div>
                <div class="info-val">github.com/eniso/analoglab-pfe</div>
            </div>
        </div>
        <div style="background:rgba(0,255,178,0.06); border:1px solid rgba(0,255,178,0.15); border-radius:12px; padding:1rem; margin-top:1rem; text-align:center;">
             <span style="color:#00FFB2; font-weight:800; font-size:0.85em;">⚡ RÉPONSE SOUS 24H</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:3rem 0; margin-top:4rem; border-top:1px solid rgba(255,255,255,0.05);">
    <p style="font-weight:900; background:linear-gradient(135deg,#00FFB2,#00B8FF); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">⚡ AnalogLab</p>
    <p style="color:#374151; font-size:0.7em;">PFE ENISO 2025–2026</p>
</div>
""", unsafe_allow_html=True)
