"""
AGENT NLP (INTERFACE STREAMLIT) — agent_interface.py
Interface principale de la plateforme de validation.
Moteur NLP : regex pattern matching (sans dépendance externe).

Intentions reconnues:
  - "courbe de [composant]"
  - "valide ia de [composant]"
  - "valide hls de [composant]"
  - "validation complète de [composant]"
  - "erreur de [composant]"
  - "génère modèle ia de [composant]"
  - "génère hls de [composant]"
  - "simule [composant]"

Lancement: streamlit run agent_interface.py
"""

import re
import os
import sys
import sqlite3
import json
import numpy as np

import streamlit as st
from utils.navbar import render_navbar

# Chemin racine du projet
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Remonté d'un niveau car dans pages/
sys.path.insert(0, ROOT)

DB_PATH = os.path.join(ROOT, "composants_db.sqlite")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration Streamlit
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AnalogLab · Plateforme de Validation",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS — Design système premium AnalogLab
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #060A14 !important;
    }
    .stApp {
        background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,178,0.06) 0%, transparent 60%),
                    #060A14 !important;
    }

    /* ── Header ── */
    .main-header {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(20px);
        padding: 1.8rem 2.5rem;
        border-radius: 18px;
        margin-bottom: 2rem;
        border: 1px solid rgba(0,255,178,0.12);
        box-shadow: 0 0 40px rgba(0,255,178,0.05), inset 0 1px 0 rgba(255,255,255,0.05);
        display: flex; align-items: center; gap: 1.5rem;
    }
    .main-header h2 {
        margin: 0;
        font-size: 1.6em; font-weight: 800; letter-spacing: -0.5px;
        background: linear-gradient(135deg, #fff, #9CA3AF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .header-badge {
        background: rgba(0,255,178,0.1); border: 1px solid rgba(0,255,178,0.25);
        color: #00FFB2; padding: 4px 14px; border-radius: 100px;
        font-size: 0.75em; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; white-space: nowrap;
    }

    /* ── Chat bubbles ── */
    .chat-user {
        background: rgba(0,184,255,0.08);
        border: 1px solid rgba(0,184,255,0.15);
        padding: 0.9rem 1.4rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0.8rem 0 0.3rem 4rem;
        text-align: right; color: #CBD5E1; font-weight: 500;
        transition: all 0.2s ease;
    }
    .chat-user:hover { border-color: rgba(0,184,255,0.3); }

    .chat-bot-header {
        background: rgba(0,255,178,0.07);
        border: 1px solid rgba(0,255,178,0.12); border-bottom: none;
        padding: 0.5rem 1.4rem 0.4rem;
        border-radius: 16px 16px 0 0;
        margin: 0.8rem 4rem 0 0;
        color: #00FFB2; font-weight: 700; font-size: 0.85em;
        letter-spacing: 1px; text-transform: uppercase;
    }
    .chat-bot-content {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(0,255,178,0.12); border-top: none;
        padding: 0.8rem 1.4rem 1rem;
        border-radius: 0 0 16px 16px;
        margin: 0 4rem 0.5rem 0;
        color: #CBD5E1; line-height: 1.65;
    }

    /* ── Badges ── */
    .pass-badge {
        background: rgba(0,255,178,0.12); color: #00FFB2;
        padding: 0.3rem 1rem; border-radius: 100px; font-weight: 700;
        border: 1px solid rgba(0,255,178,0.3);
        font-size: 0.9em;
    }
    .fail-badge {
        background: rgba(255,80,80,0.1); color: #FF6B6B;
        padding: 0.3rem 1rem; border-radius: 100px; font-weight: 700;
        border: 1px solid rgba(255,80,80,0.3);
        font-size: 0.9em;
    }
    .composant-actif {
        color: #00FFB2; font-weight: 700;
        background: rgba(0,255,178,0.1);
        padding: 0.2rem 0.8rem; border-radius: 100px;
        border: 1px solid rgba(0,255,178,0.25); display: inline-block;
    }

    /* ── Metric box ── */
    .metric-box {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
        padding: 1.2rem; border-radius: 14px; text-align: center;
    }

    /* ── Suggestion chips ── */
    .cmd-suggestion {
        display: inline-block;
        background: rgba(0,255,178,0.06); color: #00FFB2;
        padding: 0.4rem 0.9rem; margin: 0.3rem;
        border-radius: 8px; font-size: 0.82em;
        font-family: 'JetBrains Mono', monospace;
        border: 1px solid rgba(0,255,178,0.2);
        transition: all 0.2s ease;
    }
    .cmd-suggestion:hover {
        background: rgba(0,255,178,0.12);
        transform: translateY(-2px);
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #E2E8F0 !important; border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(0,255,178,0.4) !important;
        box-shadow: 0 0 0 2px rgba(0,255,178,0.1) !important;
    }
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important; color: #E2E8F0 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: rgba(6,10,20,0.97) !important;
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
    }

    /* ── Divider ── */
    hr { border-color: rgba(255,255,255,0.05) !important; }

    /* ── Code / markdown tables ── */
    code {
        background: rgba(0,255,178,0.08) !important;
        color: #00FFB2 !important;
        border-radius: 4px !important; padding: 1px 6px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stMarkdown table {
        border: 1px solid rgba(255,255,255,0.07) !important;
    }
    .stMarkdown th {
        background: rgba(0,255,178,0.08) !important;
        color: #00FFB2 !important; border: 1px solid rgba(255,255,255,0.07) !important;
    }
    .stMarkdown td {
        color: #9CA3AF !important; border: 1px solid rgba(255,255,255,0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── TOPBAR ──────────────────────────────────────────────────────────────────
render_navbar(active_page="platform")


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def get_composants_liste() -> list[str]:
    """Retourne la liste des composants disponibles en base."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nom FROM composants ORDER BY nom")
        noms = [r[0] for r in cursor.fetchall()]
        conn.close()
        return noms
    except Exception:
        return []


def init_session():
    """Initialise les variables de session Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "composant_actif" not in st.session_state:
        composants = get_composants_liste()
        st.session_state.composant_actif = composants[0] if composants else ""
    if "db_initialise" not in st.session_state:
        st.session_state.db_initialise = os.path.exists(DB_PATH)


def ajouter_message(role: str, contenu: str, figure=None):
    """Ajoute un message au chat (avec figure optionnelle)."""
    st.session_state.messages.append({
        "role": role,
        "contenu": contenu,
        "figure": figure
    })


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR NLP — Patterns regex
# ─────────────────────────────────────────────────────────────────────────────

PATTERNS = [
    # (regex, intention, description)
    (r"courbe\s+(?:de\s+|d[eu]\s+)?(.+)",
     "courbe", "Affiche la courbe I-V simulée"),

    (r"(?:g[eé]n[eè]re?|entra[iî]ne?)\s+(?:mod[eè]le\s+)?ia\s+(?:de|du|pour)\s+(.+)",
     "generer_ia", "Entraîne + valide le modèle IA"),

    (r"(?:g[eé]n[eè]re?|convertis?)\s+hls\s+(?:de|du|pour)\s+(.+)",
     "generer_hls", "Convertit + valide le modèle HLS"),

    (r"(?:valide?(?:r)?|validation)\s+ia\s+(?:de|du|pour)\s+(.+)",
     "valider_ia", "Compare simulation vs prédiction IA"),

    (r"(?:valide?(?:r)?|validation)\s+hls\s+(?:de|du|pour)\s+(.+)",
     "valider_hls", "Compare simulation vs HLS"),

    (r"validation\s+compl[eè]te?\s+(?:de|du|pour)\s+(.+)",
     "valider_complet", "Superpose les 3 courbes avec métriques"),

    (r"(?:erreurs?|m[eé]triques?)\s+(?:de|du|pour)\s+(.+)",
     "erreurs", "Affiche les métriques d'erreur"),

    (r"(?:simule?r?|simulations?)\s+(.+)",
     "simuler", "Lance la simulation SPICE"),

    (r"(?:rapport|pdf|exporte?r?)\s+(?:de|du|pour)\s+(.+)",
     "rapport", "Génère le rapport PDF"),

    (r"(?:aide|help|\?|commandes?)",
     "aide", "Affiche l'aide"),

    (r"(?:liste?r?|liste)\s+(?:les\s+)?composants?",
     "lister", "Liste les composants disponibles"),
]


def detecter_intention(texte: str) -> tuple[str, str] | tuple[None, None]:
    """
    Analyse le texte et retourne (intention, composant_nom).
    Retourne (None, None) si aucune intention reconnue.
    """
    texte_norm = texte.strip().lower()
    # Normaliser les accents pour le matching
    texte_norm = (texte_norm
                  .replace("é", "e").replace("è", "e").replace("ê", "e")
                  .replace("à", "a").replace("â", "a")
                  .replace("ç", "c").replace("î", "i").replace("û", "u")
                  .replace("ô", "o").replace("ù", "u"))

    for pattern, intention, _ in PATTERNS:
        m = re.search(pattern, texte_norm, re.IGNORECASE)
        if m:
            if m.lastindex and m.lastindex >= 1:
                composant = m.group(1).strip().upper()
            else:
                composant = st.session_state.composant_actif
            return intention, composant

    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# GESTIONNAIRE DE RÉPONSES
# ─────────────────────────────────────────────────────────────────────────────

def repondre(intention: str, composant: str) -> tuple[str, object]:
    """
    Exécute l'intention et retourne (texte_réponse, figure_ou_None).
    """
    # Vérifier que le composant existe
    composants_dispo = get_composants_liste()

    if intention in ("aide",):
        return _aide_texte(), None

    if intention in ("lister",):
        if composants_dispo:
            liste = "\n".join([f"• **{c}**" for c in composants_dispo])
            return f"Composants disponibles:\n{liste}", None
        return "Aucun composant en base. Lancez d'abord `upload_spice.py`.", None

    # Normaliser le nom du composant
    composant_reel = None
    for c in composants_dispo:
        if c.upper() == composant.upper() or composant.upper() in c.upper():
            composant_reel = c
            break

    if not composant_reel:
        # Suggérer le plus proche
        suggestion = composants_dispo[0] if composants_dispo else "aucun"
        return (f"✗ Composant '**{composant}**' introuvable. "
                f"Disponibles: {', '.join(composants_dispo) or 'aucun'}. "
                f"Chargez-le avec `python upload_spice.py --file data/{composant}_params.json`"), None

    # Mettre à jour le composant actif
    st.session_state.composant_actif = composant_reel

    try:
        if intention == "simuler":
            return _action_simuler(composant_reel)

        elif intention == "courbe":
            return _action_courbe(composant_reel)

        elif intention == "generer_ia":
            return _action_generer_ia(composant_reel)

        elif intention == "generer_hls":
            return _action_generer_hls(composant_reel)

        elif intention == "valider_ia":
            return _action_valider_ia(composant_reel)

        elif intention == "valider_hls":
            return _action_valider_hls(composant_reel)

        elif intention == "valider_complet":
            return _action_valider_complet(composant_reel)

        elif intention == "erreurs":
            return _action_erreurs(composant_reel)

        elif intention == "rapport":
            return _action_rapport(composant_reel)

    except Exception as e:
        return f"✗ Erreur: {str(e)}", None

    return "⚠ Intention non reconnue.", None


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────

def _action_simuler(nom: str):
    from simulateur import simuler
    with st.spinner(f"Simulation SPICE de {nom}..."):
        V, I = simuler(nom, force=True)
    txt = (f"✓ Simulation **{nom}** terminée.\n"
           f"• Points: **{len(V)}**\n"
           f"• I(V=0.7V) ≈ **{np.interp(0.7, V, I)*1000:.3f} mA**\n"
           f"• I(V=1.0V) ≈ **{np.interp(1.0, V, I)*1000:.3f} mA**")
    from visualiseur_validation import courbe_unique
    fig = courbe_unique(nom)
    return txt, fig


def _action_courbe(nom: str):
    from simulateur import charger_simulation, simuler
    from visualiseur_validation import courbe_unique

    data = charger_simulation(nom)
    if data is None:
        with st.spinner(f"Simulation de {nom} en cours..."):
            simuler(nom)
    fig = courbe_unique(nom)
    return f"◆ Courbe I-V de **{nom}** (simulation SPICE).", fig


def _action_generer_ia(nom: str):
    from simulateur import charger_simulation, simuler
    from trainer import entrainer
    from visualiseur_validation import validation_ia

    if charger_simulation(nom) is None:
        with st.spinner("Simulation préalable..."):
            simuler(nom)
    with st.spinner(f"Entraînement MLP pour {nom}... (peut prendre 1-2 min)"):
        entrainer(nom, force=True)
    fig = validation_ia(nom)
    return (f"◉ Modèle IA entraîné pour **{nom}**.\n"
            f"→ Voir le graphique de validation ci-dessous."), fig


def _action_generer_hls(nom: str):
    from hls_converter import convertir_hls
    from visualiseur_validation import validation_hls

    with st.spinner(f"Conversion HLS (int8) de {nom}..."):
        convertir_hls(nom, quant_type="int8", force=True)
    fig = validation_hls(nom)
    return (f"⚡ Modèle HLS (int8) généré pour **{nom}**.\n"
            f"→ Voir la comparaison ci-dessous."), fig


def _action_valider_ia(nom: str):
    from visualiseur_validation import validation_ia
    fig = validation_ia(nom)
    return f"◉ Validation IA de **{nom}** : simulation vs prédiction MLP.", fig


def _action_valider_hls(nom: str):
    from visualiseur_validation import validation_hls
    fig = validation_hls(nom)
    return f"⚡ Validation HLS de **{nom}** : simulation vs quantifié int8.", fig


def _action_valider_complet(nom: str):
    from visualiseur_validation import validation_complete
    with st.spinner(f"Validation complète de {nom}..."):
        fig = validation_complete(nom, exporter_pdf=True)
    reports_dir = os.path.join(ROOT, "reports")
    pdf_path = os.path.join(reports_dir, f"{nom}_validation.pdf")
    pdf_info = f"\n◈ Rapport PDF: `{pdf_path}`" if os.path.exists(pdf_path) else ""
    return (f"✓ Validation complète de **{nom}** :"
            f" simulation + IA + HLS superposés.{pdf_info}"), fig


def _action_erreurs(nom: str):
    from metriques import toutes_metriques, verdict_pass_fail
    import json

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM composants WHERE nom = ?", (nom,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return f"Composant '{nom}' introuvable.", None
    comp_id = row[0]

    # Simulation
    cursor.execute("SELECT V_json, I_json FROM simulations WHERE composant_id = ? "
                   "ORDER BY created_at DESC LIMIT 1", (comp_id,))
    sim = cursor.fetchone()

    # IA
    cursor.execute("SELECT V_pred_json, I_pred_json FROM modeles_ia "
                   "WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1", (comp_id,))
    ia = cursor.fetchone()

    # HLS
    cursor.execute("SELECT V_hls_json, I_hls_json FROM modeles_hls "
                   "WHERE composant_id = ? ORDER BY created_at DESC LIMIT 1", (comp_id,))
    hls = cursor.fetchone()
    conn.close()

    if not sim:
        return f"✗ Aucune simulation pour '{nom}'.", None

    V_sim = np.array(json.loads(sim[0]))
    I_sim = np.array(json.loads(sim[1]))

    lignes = [f"## ◆ Métriques d'erreur — {nom}\n"]

    if ia:
        I_pred = np.interp(V_sim, np.array(json.loads(ia[0])), np.array(json.loads(ia[1])))
        m = toutes_metriques(I_sim, I_pred)
        v = verdict_pass_fail(m["E_rel_%"], "ia")
        lignes.append(f"### ◉ Modèle IA (MLP)")
        lignes.append(f"▸ MAE: `{m['MAE']:.4e}` A")
        lignes.append(f"▸ RMSE: `{m['RMSE']:.4e}` A")
        lignes.append(f"▸ Erreur max: `{m['E_max']:.4e}` A")
        lignes.append(f"▸ Erreur rel: `{m['E_rel_%']:.3f}` %")
        lignes.append(f"▸ R²: `{m['R2']:.6f}`")
        lignes.append(f"▸ **VERDICT: {'✓ PASS' if v == 'PASS' else '✗ FAIL'}** (seuil 2%)")
        lignes.append("")

    if hls:
        I_hls = np.interp(V_sim, np.array(json.loads(hls[0])), np.array(json.loads(hls[1])))
        m = toutes_metriques(I_sim, I_hls)
        v = verdict_pass_fail(m["E_rel_%"], "hls")
        lignes.append(f"### ⚡ Modèle HLS (int8)")
        lignes.append(f"▸ MAE: `{m['MAE']:.4e}` A")
        lignes.append(f"▸ RMSE: `{m['RMSE']:.4e}` A")
        lignes.append(f"▸ Erreur max: `{m['E_max']:.4e}` A")
        lignes.append(f"▸ Erreur rel: `{m['E_rel_%']:.3f}` %")
        lignes.append(f"▸ R²: `{m['R2']:.6f}`")
        lignes.append(f"▸ **VERDICT: {'✓ PASS' if v == 'PASS' else '✗ FAIL'}** (seuil 5%)")

    if not ia and not hls:
        lignes.append("Aucun modèle entraîné. Tapez `génère modèle ia de " + nom + "`.")

    return "\n".join(lignes), None


def _action_rapport(nom: str):
    from report_generator import generer_rapport
    with st.spinner(f"Génération rapport PDF pour {nom}..."):
        path = generer_rapport(nom)
    return f"◈ Rapport PDF généré:\n`{path}`", None


def _aide_texte() -> str:
    comp_actif = st.session_state.get("composant_actif", "aucun")
    return f"""## ◈ Commandes disponibles

| Commande | Action |
|----------|--------|
| `courbe de [composant]` | Affiche la courbe I-V simulée |
| `simule [composant]` | Lance la simulation SPICE |
| `génère modèle ia de [composant]` | Entraîne le MLP + validation |
| `génère hls de [composant]` | Quantification int8 + validation |
| `valide ia de [composant]` | Compare simulation vs IA |
| `valide hls de [composant]` | Compare simulation vs HLS |
| `validation complète de [composant]` | Superpose les 3 courbes |
| `erreur de [composant]` | Affiche toutes les métriques |
| `rapport de [composant]` | Génère le rapport PDF |
| `liste composants` | Liste les composants en base |
| `aide` | Affiche cette aide |

**◆ Composant actif:** :green[{comp_actif}]
"""


# ─────────────────────────────────────────────────────────────────────────────
# INTERFACE PRINCIPALE STREAMLIT — Horizontal Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def main():
    init_session()

    # ── CSS Supplémentaire pour le layout horizontal ───────────────────────
    st.markdown("""
    <style>
    /* Cacher sidebar complètement */
    [data-testid="stSidebar"] { display:none !important; }
    header[data-testid="stHeader"] { display:none !important; }
    footer { display:none !important; }
    .block-container { padding-top:0.5rem !important; padding-bottom:0 !important; max-width:100% !important; }

    /* ── Control strip horizontal ── */
    .ctrl-strip {
        display:flex; align-items:center; gap:1rem; flex-wrap:wrap;
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
        border-radius:16px; padding:1.2rem 1.5rem; margin-bottom:1.5rem;
    }
    .ctrl-label { color:#6B7280; font-size:0.78em; font-weight:700;
        letter-spacing:1.5px; text-transform:uppercase; white-space:nowrap; }

    /* ── Chat layout ── */
    .chat-panel {
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
        border-radius:18px; padding:1.5rem;
        height: calc(100vh - 280px); overflow-y:auto;
    }
    .action-panel {
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
        border-radius:18px; padding:1.5rem; height:100%;
    }
    .action-title { color:#6B7280; font-size:0.72em; font-weight:700;
        letter-spacing:2px; text-transform:uppercase; margin-bottom:1rem; }
    .action-btn-group { display:flex; flex-direction:column; gap:0.5rem; }

    .welcome-box {
        background:rgba(0,255,178,0.04); border:1px solid rgba(0,255,178,0.1);
        border-radius:14px; padding:2rem; text-align:center; margin:1rem 0;
    }
    .comp-tag {
        background:rgba(0,255,178,0.08); border:1px solid rgba(0,255,178,0.2);
        color:#00FFB2; padding:4px 14px; border-radius:100px;
        font-size:0.85em; font-weight:700; display:inline-block; margin:0.5rem 0;
    }
    .suggestion-chip {
        display:inline-block;
        background:rgba(0,255,178,0.06); color:#00FFB2;
        padding:5px 12px; border-radius:8px; font-size:0.78em;
        font-family:'JetBrains Mono',monospace;
        border:1px solid rgba(0,255,178,0.15); margin:3px;
        cursor:pointer; transition:all 0.2s;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── INITIALISATION DB ─────────────────────────────────────────────────
    col_init, col_spacer = st.columns([2, 7])
    with col_init:
        if st.button("🗄 Initialiser / Charger la DB", use_container_width=True):
            with st.spinner("Initialisation..."):
                from upload_spice import init_db, upload_composant
                import sqlite3
                conn = sqlite3.connect(DB_PATH)
                init_db(conn); conn.close()
                data_dir = os.path.join(ROOT, "data")
                for fname in os.listdir(data_dir):
                    if fname.endswith("_params.json"):
                        upload_composant(os.path.join(data_dir, fname))
            st.success("✅ Base initialisée !")
            st.session_state.db_initialise = True
            st.rerun()

    composants = get_composants_liste()

    if not composants:
        st.markdown("""
        <div style="text-align:center;padding:4rem;background:rgba(255,184,0,0.06);
            border:1px solid rgba(255,184,0,0.15);border-radius:18px;margin:2rem 0;">
            <div style="font-size:3em;margin-bottom:1rem;">🗄</div>
            <p style="color:#FFB800;font-weight:700;font-size:1.1em;margin-bottom:0.5rem;">
                Base de données vide
            </p>
            <p style="color:#6B7280;font-size:0.9em;">
                Cliquez sur "Initialiser / Charger la DB" pour charger les composants disponibles.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── CONTROL STRIP HORIZONTAL ──────────────────────────────────────────
    st.markdown("<div class='ctrl-strip'><span class='ctrl-label'>⚙ Contrôles</span></div>",
                unsafe_allow_html=True)

    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5, ctrl6, ctrl7 = st.columns([2, 1, 1, 1, 1, 1, 1])

    with ctrl1:
        composant_sel = st.selectbox(
            "🔩 Composant actif",
            composants,
            index=composants.index(st.session_state.composant_actif)
            if st.session_state.composant_actif in composants else 0,
            label_visibility="visible"
        )
        st.session_state.composant_actif = composant_sel

    with ctrl2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Courbe I-V", use_container_width=True):
            resp, fig = repondre("courbe", composant_sel)
            ajouter_message("user", f"courbe de {composant_sel}")
            ajouter_message("bot", resp, fig); st.rerun()

    with ctrl3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔬 Simuler", use_container_width=True):
            resp, fig = repondre("simuler", composant_sel)
            ajouter_message("user", f"simule {composant_sel}")
            ajouter_message("bot", resp, fig); st.rerun()

    with ctrl4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🤖 Entraîner IA", use_container_width=True):
            resp, fig = repondre("generer_ia", composant_sel)
            ajouter_message("user", f"génère modèle ia de {composant_sel}")
            ajouter_message("bot", resp, fig); st.rerun()

    with ctrl5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ HLS int8", use_container_width=True):
            resp, fig = repondre("generer_hls", composant_sel)
            ajouter_message("user", f"génère hls de {composant_sel}")
            ajouter_message("bot", resp, fig); st.rerun()

    with ctrl6:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ Validation", use_container_width=True, type="primary"):
            resp, fig = repondre("valider_complet", composant_sel)
            ajouter_message("user", f"validation complète de {composant_sel}")
            ajouter_message("bot", resp, fig); st.rerun()

    with ctrl7:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 Rapport PDF", use_container_width=True):
            resp, fig = repondre("rapport", composant_sel)
            ajouter_message("user", f"rapport de {composant_sel}")
            ajouter_message("bot", resp, fig); st.rerun()

    # ── LAYOUT PRINCIPAL : Chat (gauche) + Panel infos (droite) ──────────
    col_chat, col_right = st.columns([2.5, 1], gap="medium")

    with col_chat:
        # ── Historique messages ──
        if not st.session_state.messages:
            comp_exemple = st.session_state.composant_actif
            st.markdown(f"""
            <div class="welcome-box">
                <div style="font-size:2.5em;margin-bottom:0.8rem;">⚡</div>
                <p style="color:#E2E8F0;font-weight:800;font-size:1.2em;margin-bottom:0.4rem;">
                    Bienvenue sur AnalogLab
                </p>
                <p style="color:#6B7280;font-size:0.9em;margin-bottom:1rem;">
                    Plateforme de validation automatisée · ENISO PFE 2025–2026
                </p>
                <div class="comp-tag">🔩 Composant actif: {comp_exemple}</div>
                <p style="color:#374151;font-size:0.82em;margin:1rem 0 0.5rem;">
                    Commandes rapides :
                </p>
                <div>
                    <span class="suggestion-chip">courbe de {comp_exemple}</span>
                    <span class="suggestion-chip">simule {comp_exemple}</span>
                    <span class="suggestion-chip">génère modèle ia de {comp_exemple}</span>
                    <span class="suggestion-chip">validation complète de {comp_exemple}</span>
                    <span class="suggestion-chip">aide</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user">▸ {msg["contenu"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown('<div class="chat-bot-header">⚡ AnalogLab Assistant</div>',
                                unsafe_allow_html=True)
                    st.markdown('<div class="chat-bot-content">', unsafe_allow_html=True)
                    st.markdown(msg["contenu"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    if msg.get("figure") is not None:
                        st.pyplot(msg["figure"])

        # ── Input ──
        st.divider()
        with st.form("chat_form", clear_on_submit=True):
            col_input, col_btn = st.columns([6, 1])
            with col_input:
                user_input = st.text_input(
                    "Message",
                    placeholder=f'Ex: "courbe de {composant_sel}" · "validation complète de {composant_sel}" · "aide"',
                    label_visibility="collapsed"
                )
            with col_btn:
                submitted = st.form_submit_button("→", use_container_width=True, type="primary")

        if submitted and user_input.strip():
            intention, composant = detecter_intention(user_input)
            ajouter_message("user", user_input)
            if intention is None:
                ajouter_message("bot",
                    f"⚠ Je n'ai pas compris `{user_input}`.\nTapez `aide` pour voir les commandes.")
            else:
                rep_txt, rep_fig = repondre(intention, composant)
                ajouter_message("bot", rep_txt, rep_fig)
            st.rerun()

    with col_right:
        # ── Panneau d'infos / suggestions rapides ──
        st.markdown(f"""
        <div class="action-panel">
            <div class="action-title">📋 État du système</div>
            <div style="background:rgba(0,255,178,0.06);border:1px solid rgba(0,255,178,0.12);
                border-radius:12px;padding:1rem;margin-bottom:1rem;">
                <div style="color:#6B7280;font-size:0.72em;font-weight:700;letter-spacing:1px;
                    text-transform:uppercase;margin-bottom:0.5rem;">Composant actif</div>
                <div style="color:#00FFB2;font-weight:900;font-size:1.3em;">{composant_sel}</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;margin-bottom:1rem;">
                <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                    border-radius:10px;padding:0.8rem;text-align:center;">
                    <div style="color:#00FFB2;font-weight:900;font-size:1.4em;">{len(composants)}</div>
                    <div style="color:#374151;font-size:0.68em;font-weight:700;text-transform:uppercase;letter-spacing:1px;">Composants</div>
                </div>
                <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                    border-radius:10px;padding:0.8rem;text-align:center;">
                    <div style="color:#00FFB2;font-weight:900;font-size:1.4em;">{len(st.session_state.messages)}</div>
                    <div style="color:#374151;font-size:0.68em;font-weight:700;text-transform:uppercase;letter-spacing:1px;">Messages</div>
                </div>
            </div>
            <div class="action-title" style="margin-top:1rem;">📖 Aide rapide</div>
            <div style="font-size:0.78em;color:#6B7280;line-height:1.9;">
                <code style="color:#00FFB2;">courbe de X</code> → Courbe I-V<br>
                <code style="color:#00FFB2;">simule X</code> → SPICE<br>
                <code style="color:#00FFB2;">génère modèle ia de X</code> → MLP<br>
                <code style="color:#00FFB2;">génère hls de X</code> → FPGA<br>
                <code style="color:#00FFB2;">validation complète de X</code> → Tout<br>
                <code style="color:#00FFB2;">erreur de X</code> → Métriques<br>
                <code style="color:#00FFB2;">rapport de X</code> → PDF<br>
                <code style="color:#00FFB2;">aide</code> → Toutes les commandes
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Vider le chat", use_container_width=True):
            st.session_state.messages = []; st.rerun()


if __name__ == "__main__":
    main()

