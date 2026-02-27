"""
AnalogLab - Partie Numérique (Model -> HLS Project)
"""

import json
import os

import streamlit as st

from digital_hls_service import generate_hls_project_from_model, save_uploaded_model
from utils.navbar import render_navbar

st.set_page_config(
    page_title="Partie Numérique | AnalogLab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family:'Inter',sans-serif !important; background-color:#060A14 !important; }
    .stApp {
        background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,178,0.07) 0%, transparent 55%),
                    #060A14 !important;
    }
    .block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    footer { display: none !important; }

    .page-hero { padding:5rem 2rem 2.5rem; text-align:center; position:relative; }
    .hero-title {
        font-size:clamp(2.2rem,5.5vw,4.2rem);
        font-weight:900;
        letter-spacing:-1.5px;
        background:linear-gradient(135deg,#00FFB2 10%,#00B8FF 60%);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        line-height:1.1;
        margin-bottom:1rem;
    }
    .hero-sub {
        color:#6B7280;
        font-size:1.06em;
        max-width:980px;
        margin:0 auto;
        line-height:1.75;
        text-align:center;
    }

    .section-card {
        background:rgba(255,255,255,0.03);
        border:1px solid rgba(255,255,255,0.08);
        border-radius:18px;
        padding:1.4rem;
        margin-bottom:1rem;
    }

    .kpi-chip {
        background:rgba(0,255,178,0.08);
        border:1px solid rgba(0,255,178,0.22);
        color:#00FFB2;
        border-radius:10px;
        padding:0.55rem 0.8rem;
        font-weight:700;
        font-size:0.9em;
    }

    @media (max-width: 900px) {
        .page-hero { padding: 2.6rem 0.8rem 1.6rem; }
        .hero-title { font-size: clamp(1.8rem, 10vw, 2.4rem); letter-spacing: -1px; }
        .hero-sub { font-size: 0.95em; }
        .section-card { padding: 1rem; border-radius: 14px; }
        .kpi-chip { width: 100%; text-align: center; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_navbar(active_page="digital")

st.markdown(
    """
    <div class="page-hero">
        <div class="hero-title">Model IA vers HLS</div>
        <p class="hero-sub" style="text-align:center !important; margin-left:auto; margin-right:auto; max-width:980px; width:100%;">
            Chargez un modèle IA Keras (.keras/.h5), configurez la cible FPGA et générez automatiquement
            un <strong style="color:#9CA3AF;">projet HLS</strong> prêt à l'intégration.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.25, 1], gap="large")

with left:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Configuration de génération")

    uploaded_model = st.file_uploader(
        "Modèle IA (Keras)",
        type=["keras", "h5"],
        help="Formats supportés pour la V1 : .keras et .h5",
    )

    model_alias = st.text_input("Nom du modèle", placeholder="ex: cnn_motor_fault")

    c1, c2 = st.columns(2)
    with c1:
        target_part = st.text_input("FPGA Part", value="xc7a35tcpg236-1")
        precision = st.selectbox(
            "Précision",
            ["ap_fixed<16,6>", "ap_fixed<12,4>", "ap_int<8>"],
            index=0,
        )
    with c2:
        clock_period = st.number_input("Clock period (ns)", min_value=1.0, max_value=50.0, value=10.0, step=0.5)
        io_type = st.selectbox("I/O Type", ["io_parallel", "io_stream"], index=0)

    generate = st.button("🚀 Générer projet HLS", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if generate:
        if uploaded_model is None:
            st.warning("Veuillez charger un modèle .keras ou .h5.")
        else:
            with st.spinner("Génération HLS en cours..."):
                try:
                    stored_model_path, safe_name = save_uploaded_model(uploaded_model, model_alias or None)
                    result = generate_hls_project_from_model(
                        model_path=stored_model_path,
                        model_name=model_alias or safe_name,
                        target_part=target_part,
                        clock_period=float(clock_period),
                        precision=precision,
                        io_type=io_type,
                    )
                    st.session_state["digital_hls_result"] = result
                    st.success("Projet HLS généré avec succès.")
                except Exception as exc:
                    st.error(f"Échec génération HLS: {exc}")

with right:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 Rapport Ressources / Latence")

    result = st.session_state.get("digital_hls_result")
    if not result:
        st.info("Aucun résultat pour le moment. Lancez une génération.")
    else:
        st.markdown(
            f"""
            <div style="display:flex;flex-wrap:wrap;gap:0.6rem;margin-bottom:0.8rem;">
                <span class="kpi-chip">Engine: {result['engine']}</span>
                <span class="kpi-chip">Precision: {result['precision']}</span>
                <span class="kpi-chip">Clock: {result['clock_period']} ns</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        resources = result.get("resources", {})
        latency = result.get("latency", {})

        m1, m2 = st.columns(2)
        with m1:
            st.metric("Paramètres", f"{resources.get('params_total', 0):,}")
            st.metric("MAC ops", f"{resources.get('mac_operations', 0):,}")
            st.metric("DSP estimés", resources.get("estimated_dsp", 0))
        with m2:
            st.metric("BRAM18 estimées", resources.get("estimated_bram18", 0))
            st.metric("Latence (cycles)", f"{latency.get('estimated_cycles', 0):,}")
            st.metric("Latence (µs)", latency.get("estimated_latency_us", 0.0))

        st.caption("Estimation analytique initiale; la synthèse finale dépendra de l’outil FPGA.")

        if os.path.exists(result["zip_path"]):
            with open(result["zip_path"], "rb") as f:
                st.download_button(
                    "⬇️ Télécharger le projet HLS (ZIP)",
                    data=f.read(),
                    file_name=os.path.basename(result["zip_path"]),
                    mime="application/zip",
                    use_container_width=True,
                )

        with st.expander("Voir les détails JSON"):
            st.code(json.dumps(result, indent=2, ensure_ascii=False), language="json")

    st.markdown("</div>", unsafe_allow_html=True)
