"""
AnalogLab - Dashboard Principal
École Nationale d'Ingénieurs de Sousse (ENISO) · PFE 2025–2026
Design: Horizontal Dashboard + SVG Animé + Compteurs JS
"""
import streamlit as st
from utils.navbar import render_navbar

st.set_page_config(
    page_title="AnalogLab · ENISO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"   # ← pas de sidebar sur l'accueil
)

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM GLOBAL — Horizontal Dashboard Style
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family:'Inter',sans-serif !important; }

/* ── FOND GLOBAL ── */
.stApp {
    background: #060A14;
    min-height: 100vh;
}

/* ── CACHER padding streamlit par défaut ── */
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
header[data-testid="stHeader"] { display: none; }
footer { display: none !important; }

/* ── HERO SECTION ── */
.hero-section {
    position: relative; overflow: hidden;
    min-height: 92vh; display: flex; align-items: center;
    padding: 0 3rem;
}
.hero-bg-canvas {
    position: absolute; inset: 0; z-index: 0; overflow: hidden;
}
.hero-grid {
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(0,255,178,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,178,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 0%, transparent 100%);
}
.hero-glow-1 {
    position: absolute; top: -200px; left: -200px;
    width: 700px; height: 700px; border-radius: 50%;
    background: radial-gradient(circle, rgba(0,255,178,0.12) 0%, transparent 70%);
    animation: float1 8s ease-in-out infinite;
}
.hero-glow-2 {
    position: absolute; bottom: -150px; right: -100px;
    width: 600px; height: 600px; border-radius: 50%;
    background: radial-gradient(circle, rgba(0,184,255,0.1) 0%, transparent 70%);
    animation: float2 10s ease-in-out infinite;
}
@keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(40px,-30px)} }
@keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-30px,40px)} }

.hero-content {
    position: relative; z-index: 1;
    display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center;
    max-width: 1400px; margin: 0 auto; width: 100%; padding: 6rem 0;
}
.hero-left {}
.hero-phase-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(180,95,255,0.1); border: 1px solid rgba(180,95,255,0.3);
    color: #C084FC; padding: 6px 18px; border-radius: 100px;
    font-size: 0.76em; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    margin-bottom: 2rem;
}
.badge-pulse {
    width: 7px; height: 7px; background: #C084FC; border-radius: 50%;
    box-shadow: 0 0 8px #C084FC; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{box-shadow:0 0 4px #C084FC} 50%{box-shadow:0 0 16px #C084FC, 0 0 30px rgba(180,95,255,0.4)} }

.hero-title {
    font-size: clamp(2.8rem, 5.5vw, 5rem); font-weight: 900;
    line-height: 1.05; letter-spacing: -2.5px;
    color: #F9FAFB; margin-bottom: 1.5rem;
}
.hero-title .accent {
    background: linear-gradient(135deg, #00FFB2 20%, #00B8FF 80%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-desc {
    color: #6B7280; font-size: 1.1em; line-height: 1.8; max-width: 500px;
    margin-bottom: 2.5rem;
}
.hero-desc strong { color: #9CA3AF; }
.hero-tags {
    display: flex; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 2.5rem;
}
.hero-tag {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    color: #6B7280; padding: 5px 14px; border-radius: 100px; font-size: 0.8em;
    font-weight: 600; display: flex; align-items: center; gap: 6px;
}

/* ── CIRCUIT SVG PANEL ── */
.hero-right {
    display: flex; align-items: center; justify-content: center;
}
.circuit-panel {
    width: 100%; max-width: 520px; position: relative;
}
.circuit-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,178,0.12);
    border-radius: 24px; padding: 2rem; position: relative; overflow: hidden;
    box-shadow: 0 0 60px rgba(0,255,178,0.06), inset 0 1px 0 rgba(255,255,255,0.05);
}
.circuit-title {
    color: #6B7280; font-size: 0.75em; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 1rem;
}
.metrics-row {
    display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; margin-bottom: 1.5rem;
}
.metric-item {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 1rem; text-align: center;
}
.m-val {
    font-size: 1.8em; font-weight: 900; line-height: 1;
    background: linear-gradient(135deg,#00FFB2,#00B8FF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.m-lbl { color: #374151; font-size: 0.7em; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; margin-top: 5px; }
.progress-item { margin-bottom: 0.9rem; }
.prog-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.prog-label { color: #6B7280; font-size: 0.82em; font-weight: 600; }
.prog-val { color: #00FFB2; font-size: 0.82em; font-weight: 700; }
.prog-bar {
    height: 5px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden;
}
.prog-fill {
    height: 100%; border-radius: 10px;
    background: linear-gradient(90deg,#00FFB2,#00B8FF);
    animation: fillBar 2s ease-out forwards;
    transform-origin: left;
}
@keyframes fillBar { from{width:0!important} }
.status-row {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(0,255,178,0.06); border: 1px solid rgba(0,255,178,0.12);
    border-radius: 10px; padding: 0.7rem 1rem; margin-top: 1rem;
}
.status-dot { width:8px; height:8px; background:#00FFB2; border-radius:50%;
    box-shadow:0 0 8px #00FFB2; animation:pulse 2s infinite; }
.status-txt { color:#00FFB2; font-size:0.82em; font-weight:700; }
.status-eniso { color:#374151; font-size:0.75em; }

/* ── STATS STRIP ── */
.stats-strip {
    display: flex; justify-content: center; gap: 0; flex-wrap: nowrap;
    background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.stat-item {
    flex: 1; text-align: center; padding: 2rem 1.5rem;
    border-right: 1px solid rgba(255,255,255,0.04);
    transition: background 0.3s ease;
    cursor: default;
}
.stat-item:last-child { border-right: none; }
.stat-item:hover { background: rgba(0,255,178,0.03); }
.stat-num {
    font-size: 2.8em; font-weight: 900; line-height: 1; letter-spacing: -1px;
    background: linear-gradient(135deg,#00FFB2,#00B8FF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.stat-lbl { color: #374151; font-size: 0.72em; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; margin-top: 6px; }

/* ── HOW IT WORKS ── */
.how-section {
    padding: 6rem 3rem; max-width: 1400px; margin: 0 auto;
}
.section-eyebrow {
    color: #00FFB2; font-size: 0.75em; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; margin-bottom: 0.8rem;
}
.section-h { font-size: 2.6em; font-weight: 900; letter-spacing: -1px;
    color: #F9FAFB; margin-bottom: 1rem; line-height: 1.15; }
.section-p { color: #6B7280; font-size: 1em; line-height: 1.75; max-width: 550px; }

/* Steps horizontal */
.steps-row {
    display: grid; grid-template-columns: repeat(4,1fr); gap: 1.5rem;
    margin-top: 4rem;
}
.step-card {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; padding: 2rem; position: relative; overflow: hidden;
    transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
}
.step-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:20px 20px 0 0;
    background:var(--accent);
}
.step-card:hover { transform: translateY(-8px);
    box-shadow: 0 25px 50px rgba(0,0,0,0.4); border-color: rgba(0,255,178,0.15); }
.step-num {
    font-size: 3.5em; font-weight: 900; line-height: 1;
    color: rgba(255,255,255,0.18); margin-bottom: 1rem; letter-spacing: -2px;
    text-shadow: 0 0 18px rgba(255,255,255,0.12);
    -webkit-text-stroke: 1px rgba(255,255,255,0.14);
}
.step-card:hover .step-num {
    color: rgba(255,255,255,0.28);
    text-shadow: 0 0 24px rgba(255,255,255,0.18);
}
.step-icon {
    width: 48px; height: 48px; border-radius: 14px; display: flex;
    align-items: center; justify-content: center; font-size: 1.4em;
    margin-bottom: 1.2rem; border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.04);
}
.step-title { color: #E2E8F0; font-size: 1.05em; font-weight: 800; margin-bottom: 0.5rem; }
.step-desc { color: #6B7280; font-size: 0.85em; line-height: 1.6; }

/* ── IDEATION CTA ── */
.idea-cta-section {
    margin: 0 3rem 6rem; border-radius: 24px; position: relative; overflow: hidden;
    background: linear-gradient(135deg, rgba(180,95,255,0.08) 0%, rgba(0,184,255,0.06) 100%);
    border: 1px solid rgba(180,95,255,0.18); padding: 4rem;
}
.idea-cta-section::before {
    content:''; position:absolute; top:-100px; right:-100px;
    width:400px; height:400px; border-radius:50%;
    background: radial-gradient(circle, rgba(180,95,255,0.12) 0%, transparent 70%);
    pointer-events:none;
}
.idea-cta-section::after {
    content:''; position:absolute; bottom:-100px; left:-100px;
    width:400px; height:400px; border-radius:50%;
    background: radial-gradient(circle, rgba(0,184,255,0.1) 0%, transparent 70%);
    pointer-events:none;
}
.cta-inner { position:relative; z-index:1; display:grid; grid-template-columns:1fr auto; gap:3rem; align-items:center; }
.cta-label { color:#C084FC; font-size:0.75em; font-weight:700; letter-spacing:3px; text-transform:uppercase; margin-bottom:0.8rem; }
.cta-title { font-size:2.2em; font-weight:900; letter-spacing:-1px; color:#F9FAFB; margin-bottom:0.8rem; }
.cta-desc { color:#6B7280; font-size:0.95em; line-height:1.7; max-width:500px; }

/* ── FOOTER ── */
.page-footer {
    border-top: 1px solid rgba(255,255,255,0.04); padding: 2rem 3rem;
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
}
.footer-logo { font-weight:900; font-size:1.1em; letter-spacing:-0.5px;
    background:linear-gradient(135deg,#00FFB2,#00B8FF);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.footer-copy { color:#374151; font-size:0.8em; }
.footer-links { display:flex; gap:1.5rem; }
.footer-link { color:#4B5563; font-size:0.8em; text-decoration:none; transition:color 0.2s; }
.footer-link:hover { color:#00FFB2; }

/* ── STREAMLIT BUTTON OVERRIDES ── */
.stButton > button {
    background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important;
    color: #9CA3AF !important; border-radius: 12px !important; font-weight: 600 !important;
    transition: all 0.25s ease !important; letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    background: rgba(0,255,178,0.07) !important; border-color: rgba(0,255,178,0.28) !important;
    color: #00FFB2 !important; transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#00FFB2,#00B8FF) !important; border:none !important;
    color: #060A14 !important; font-weight: 800 !important;
    box-shadow: 0 0 25px rgba(0,255,178,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 40px rgba(0,255,178,0.45) !important; transform: translateY(-3px) !important;
}
hr { border-color: rgba(255,255,255,0.05) !important; }
[data-testid="stSidebar"] { display: none !important; }

@media (max-width: 900px) {
    .hero-section { min-height: auto; padding: 0 1rem; }
    .hero-content { grid-template-columns: 1fr; gap: 1.5rem; padding: 2.5rem 0; }
    .hero-title { font-size: clamp(2rem, 9vw, 2.8rem); }
    .hero-desc { font-size: 0.95em; max-width: 100%; }
    .metrics-row { grid-template-columns: 1fr; }
    .stats-strip { flex-wrap: wrap; }
    .stat-item { min-width: 50%; padding: 1.2rem 0.8rem; border-right: none; border-bottom: 1px solid rgba(255,255,255,0.04); }
    .how-section { padding: 3rem 1rem; }
    .steps-row { grid-template-columns: 1fr; margin-top: 2rem; }
    .idea-cta-section { margin: 0 1rem 3rem; padding: 2rem 1.2rem; }
    .cta-inner { grid-template-columns: 1fr; gap: 1rem; }
    .page-footer { padding: 1.5rem 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ─── NAVBAR ──────────────────────────────────────────────────────────────────
render_navbar(active_page="home")

# ─── HERO — Layout Horizontal ────────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
    <div class="hero-bg-canvas">
        <div class="hero-grid"></div>
        <div class="hero-glow-1"></div>
        <div class="hero-glow-2"></div>
    </div>
    <div class="hero-content">
        <!-- GAUCHE : Texte -->
        <div class="hero-left">
            <div class="hero-phase-badge">
                <div class="badge-pulse"></div>
                Phase Idéation Active · ENISO
            </div>
            <div class="hero-title">
                Valider l'Électronique<br>
                avec <span class="accent">l'IA &amp; le HLS</span><br>
            </div>
            <p class="hero-desc">
                <strong>AnalogLab</strong> est une plateforme de validation automatisée
                de composants électroniques analogiques — développée à l'
                <strong>École Nationale d'Ingénieurs de Sousse</strong>.
                SPICE · Réseau de Neurones · FPGA.<br>
                <strong>Nouveau :</strong> un module numérique permet de convertir un modèle IA
                (<code>.keras/.h5</code>) en <strong>projet HLS</strong> prêt à l'intégration.
            </p>
            <div class="hero-tags">
                <span class="hero-tag">📊 Simulation SPICE</span>
                <span class="hero-tag">🤖 MLP Neural Network</span>
                <span class="hero-tag">⚡ HLS / FPGA</span>
                <span class="hero-tag">🧠 Model IA vers HLS</span>
                <span class="hero-tag">📄 Rapport PDF</span>
                <span class="hero-tag">🎓 ENISO PFE</span>
            </div>
        </div>
        <!-- DROITE : Dashboard card animée -->
        <div class="hero-right">
            <div class="circuit-panel">
                <div class="circuit-card">
                    <div class="circuit-title">📊 Validation Dashboard · Live</div>
                    <div class="metrics-row">
                        <div class="metric-item">
                            <div class="m-val" id="cnt1">4+</div>
                            <div class="m-lbl">Composants</div>
                        </div>
                        <div class="metric-item">
                            <div class="m-val" id="cnt2">98%</div>
                            <div class="m-lbl">Précision IA</div>
                        </div>
                        <div class="metric-item">
                            <div class="m-val" id="cnt3">3</div>
                            <div class="m-lbl">Technologies</div>
                        </div>
                    </div>
                    <div class="progress-item">
                        <div class="prog-header">
                            <span class="prog-label">🔬 Simulation SPICE</span>
                            <span class="prog-val">100%</span>
                        </div>
                        <div class="prog-bar"><div class="prog-fill" style="width:100%"></div></div>
                    </div>
                    <div class="progress-item">
                        <div class="prog-header">
                            <span class="prog-label">🤖 Modèle IA (MLP)</span>
                            <span class="prog-val">98.2%</span>
                        </div>
                        <div class="prog-bar"><div class="prog-fill" style="width:98.2%"></div></div>
                    </div>
                    <div class="progress-item">
                        <div class="prog-header">
                            <span class="prog-label">⚡ Synthèse HLS (int8)</span>
                            <span class="prog-val">95.7%</span>
                        </div>
                        <div class="prog-bar"><div class="prog-fill" style="width:95.7%"></div></div>
                    </div>
                    <div class="progress-item">
                        <div class="prog-header">
                            <span class="prog-label">📄 Export Rapport PDF</span>
                            <span class="prog-val">100%</span>
                        </div>
                        <div class="prog-bar"><div class="prog-fill" style="width:100%"></div></div>
                    </div>
                    <div class="status-row">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <div class="status-dot"></div>
                            <span class="status-txt">Système opérationnel</span>
                        </div>
                        <span class="status-eniso">ENISO · 2025–2026</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
// Compteurs animés
function animateCount(id, target, suffix, duration) {
    const el = document.getElementById(id);
    if (!el) return;
    let start = 0; const step = target / (duration / 16);
    const timer = setInterval(() => {
        start += step;
        if (start >= target) { el.textContent = target + suffix; clearInterval(timer); }
        else { el.textContent = Math.floor(start) + suffix; }
    }, 16);
}
setTimeout(() => {
    animateCount('cnt1', 4, '+', 1200);
    animateCount('cnt2', 98, '%', 1500);
    animateCount('cnt3', 3, '', 1000);
}, 400);
</script>
""", unsafe_allow_html=True)

# ─── STATS STRIP ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="stats-strip">
    <div class="stat-item">
        <div class="stat-num">4+</div>
        <div class="stat-lbl">Composants validés</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">&lt;2%</div>
        <div class="stat-lbl">Erreur IA moyenne</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">3</div>
        <div class="stat-lbl">Technologies</div>
    </div>
    <div class="stat-item">
        <div class="stat-num">2026</div>
        <div class="stat-lbl">Année de lancement</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── HOW IT WORKS (4 steps horizontaux) ──────────────────────────────────────
st.markdown("""
<div class="how-section">
    <div class="section-eyebrow">Comment ça marche</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 4rem;">
        <div>
            <div class="section-h">Un workflow<br>d'ingénierie intelligent.</div>
        </div>
        <div style="display:flex;align-items:center;">
            <p class="section-p">
                AnalogLab automatise la chaîne complète : de la simulation SPICE à la prédiction
                IA, jusqu'à la synthèse FPGA — avec génération de rapport en un clic.
            </p>
        </div>
    </div>
    <div class="steps-row">
        <div class="step-card" style="--accent:linear-gradient(90deg,#00FFB2,#00B8FF)">
            <div class="step-num">01</div>
            <div class="step-icon">📂</div>
            <div class="step-title">Import Composant</div>
            <div class="step-desc">Chargez les paramètres SPICE du composant (diode, BJT…) via l'interface ou l'upload.</div>
        </div>
        <div class="step-card" style="--accent:linear-gradient(90deg,#00B8FF,#B45FFF)">
            <div class="step-num">02</div>
            <div class="step-icon">🔬</div>
            <div class="step-title">Simulation SPICE</div>
            <div class="step-desc">Le moteur génère la courbe I-V de référence avec points de fonctionnement précis.</div>
        </div>
        <div class="step-card" style="--accent:linear-gradient(90deg,#B45FFF,#FF6B9D)">
            <div class="step-num">03</div>
            <div class="step-icon">🤖</div>
            <div class="step-title">Entraînement IA</div>
            <div class="step-desc">Un réseau MLP est entraîné pour prédire le comportement — erreur &lt; 2%.</div>
        </div>
        <div class="step-card" style="--accent:linear-gradient(90deg,#FFB800,#FF6B00)">
            <div class="step-num">04</div>
            <div class="step-icon">📄</div>
            <div class="step-title">Rapport &amp; HLS</div>
            <div class="step-desc">Synthèse HLS (int8) + rapport PDF automatique avec toutes les métriques.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── IDEATION CTA ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="idea-cta-section">
    <div class="cta-inner">
        <div>
            <div class="cta-label">🧪 Phase Idéation Ouverte</div>
            <div class="cta-title">Vous avez une idée<br>pour AnalogLab ?</div>
            <p class="cta-desc">
                Le projet est en construction à l'ENISO. Chaque suggestion d'ingénieur,
                étudiant ou professeur compte pour définir le produit final.
            </p>
        </div>
        <div style="display:flex;flex-direction:column;gap:0.8rem;min-width:200px;position:relative;z-index:1;">
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

_, col_x, col_y, col_z, _ = st.columns([0.7, 1.1, 1.1, 1.1, 0.7])
with col_x:
    if st.button("💡 Partagez vos idées →", use_container_width=True, type="primary"):
        st.switch_page("pages/recommendations.py")
with col_y:
    if st.button("⚙ Essayer l'Analogique", use_container_width=True):
        st.switch_page("pages/agent_interface.py")
with col_z:
    if st.button("🧠 Partie Numérique", use_container_width=True):
        st.switch_page("pages/digital_hls.py")

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-footer">
    <div>
        <div class="footer-logo">⚡ AnalogLab</div>
        <div class="footer-copy">École Nationale d'Ingénieurs de Sousse (ENISO) · PFE 2025–2026</div>
    </div>
</div>
""", unsafe_allow_html=True)
