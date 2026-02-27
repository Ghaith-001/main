"""
AnalogLab - À Propos / Vision / Idéation
École Nationale d'Ingénieurs de Sousse (ENISO) — PFE 2025-2026
"""
import streamlit as st
from utils.navbar import render_navbar

st.set_page_config(
    page_title="À Propos & Vision | AnalogLab",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── DESIGN SYSTEM (Identique à app.py pour la cohérence) ────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] { font-family:'Inter',sans-serif !important; background-color:#060A14 !important; }
.stApp {
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,178,0.07) 0%, transparent 55%),
                #060A14 !important;
}

/* Cacher éléments Streamlit */
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
footer { display: none !important; }

/* Page hero */
.page-hero { padding: 5rem 2rem 4rem; text-align: center; position: relative; }
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
    font-size:0.78em; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:1.8rem;
}
.badge-dot { width:7px; height:7px; background:#C084FC; border-radius:50%;
    box-shadow:0 0 8px #C084FC; animation:blink 1.8s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.25} }
.page-title {
    font-size:clamp(2.5rem,6vw,4.5rem); font-weight:900; letter-spacing:-2px;
    background:linear-gradient(135deg,#fff 20%,#9CA3AF 80%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    line-height:1.1; margin-bottom:1rem;
}
.page-sub {
    color:#6B7280;
    font-size:1.1em;
    max-width:600px;
    margin:0 auto;
    line-height:1.7;
    text-align:center !important;
    width:100%;
}

/* Cards */
.info-card {
    background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
    border-radius:20px; padding:2.2rem; height:100%;
    transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
    position:relative; overflow:hidden;
}
.info-card::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:20px 20px 0 0; }
.cv::after { background:linear-gradient(90deg,#00FFB2,#00B8FF); }
.cw::after { background:linear-gradient(90deg,#B45FFF,#FF6B9D); }
.cg::after { background:linear-gradient(90deg,#FFB800,#FF6B00); }
.ci::after { background:linear-gradient(90deg,#00B8FF,#B45FFF); }
.info-card:hover {
    transform:translateY(-8px); border-color:rgba(0,255,178,0.15);
    box-shadow:0 25px 50px rgba(0,0,0,0.4), 0 0 30px rgba(0,255,178,0.05);
}
.card-icon { font-size:2em; margin-bottom:1rem; display:block; }
.card-title { font-size:1.35em; font-weight:800; color:#F9FAFB; margin-bottom:0.8rem; letter-spacing:-0.5px; }
.card-text { color:#6B7280; font-size:0.95em; line-height:1.75; }
.card-text strong { color:#E2E8F0; }

/* UI overrides footer buttons */
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
render_navbar(active_page="about")

# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
    <div class="hero-glow"></div>
    <div class="hero-rel">
        <div class="badge"><div class="badge-dot"></div>ENISO · PFE 2025–2026</div>
        <div class="page-title">Redefining<br>Hardware Validation</div>
        <p class="page-sub" style="text-align:center !important; margin-left:auto; margin-right:auto; max-width:600px; width:100%;">
            De l'<strong style="color:#9CA3AF;">École Nationale d'Ingénieurs de Sousse (ENISO)</strong>
            vers l'industrie deep-tech mondiale.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── PHASE BANNER ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(180,95,255,0.08),rgba(0,184,255,0.06));
    border:1px solid rgba(180,95,255,0.2); border-radius:16px;
    padding:1.5rem 2rem; margin:3rem 0; display:flex; align-items:center; gap:1.5rem;">
    <div style="width:12px; height:12px; background:#B45FFF; border-radius:50%;
        box-shadow:0 0 12px #B45FFF; flex-shrink:0; animation:blink 2s infinite;"></div>
    <div>
        <strong style="color:#C084FC;font-size:1em;">🧪 Phase Idéation — Active & Ouverte</strong><br>
        <span style="color:#6B7280;font-size:0.92em;">
            Chaque idée compte. Vos suggestions guident directement la roadmap.
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── 4 CARDS ─────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("""
    <div class="info-card cv">
        <span class="card-icon">🔭</span>
        <div class="card-title">Notre Vision</div>
        <div class="card-text">
            Un ingénieur hardware ne devrait pas passer des semaines à valider manuellement
            un composant. <strong>AnalogLab aspire</strong> à devenir l'assistant intelligent
            universel.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card cg">
        <span class="card-icon">🎯</span>
        <div class="card-title">Le But</div>
        <div class="card-text">
            <strong>Court terme (PFE ENISO) :</strong> Valider la faisabilité d'une approche hybride.<br><br>
            <strong>Moyen terme (Startup) :</strong> SaaS proposé aux startups deep-tech.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="info-card cw">
        <span class="card-icon">💡</span>
        <div class="card-title">Pourquoi AnalogLab ?</div>
        <div class="card-text">
            La validation analogique est <strong>lente et coûteuse</strong>. Pas d'outil unifié IA + matériel.
            Nous comblons ce vide.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card ci">
        <span class="card-icon">🧠</span>
        <div class="card-title">Participez à l'Idéation</div>
        <div class="card-text">
            Ingénieurs, étudiants, professeurs — vos propositions guident les prochaines features.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── ROADMAP ─────────────────────────────────────────────────────────────────
st.markdown("<h3 style='color:#F9FAFB;font-weight:800;letter-spacing:-0.5px;'>🗺️ Roadmap</h3>", unsafe_allow_html=True)
cr1, cr2 = st.columns(2, gap="large")
with cr1:
    st.markdown("""
    <div style="display:flex;gap:1rem;margin-bottom:1rem;">
        <span style="background:rgba(0,255,178,0.1); color:#00FFB2; padding:4px 12px; border-radius:100px; font-weight:800; font-size:0.8em;">2025</span>
        <div style="color:#6B7280; font-size:0.9em;"><b>Prototype ENISO :</b> Développement plateforme core.</div>
    </div>
    """, unsafe_allow_html=True)
with cr2:
     st.markdown("""
    <div style="display:flex;gap:1rem;margin-bottom:1rem;">
        <span style="background:rgba(0,184,255,0.1); color:#00B8FF; padding:4px 12px; border-radius:100px; font-weight:800; font-size:0.8em;">2026+</span>
        <div style="color:#6B7280; font-size:0.9em;"><b>Startup Mode :</b> Levée de fonds & industrialisation.</div>
    </div>
    """, unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:3rem 0; border-top:1px solid rgba(255,255,255,0.05); margin-top:4rem;">
    <p style="font-weight:900; background:linear-gradient(135deg,#00FFB2,#00B8FF); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">⚡ AnalogLab</p>
    <p style="color:#374151; font-size:0.8em;">École Nationale d'Ingénieurs de Sousse · 2025–2026</p>
</div>
""", unsafe_allow_html=True)
