import streamlit as st

st.set_page_config(page_title="AnalogLab - Redirection", page_icon="⚡")

st.warning("### 🔄 Architecture mise à jour")
st.write("""
La structure du projet a été optimisée pour supporter la navigation multi-page (Dashboard Horizontal).
Le fichier principal est désormais **`app.py`**.
""")

col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Aller à l'Accueil", use_container_width=True, type="primary"):
        st.switch_page("app.py")
with col2:
    if st.button("⚙ Aller à la Plateforme", use_container_width=True):
        st.switch_page("pages/agent_interface.py")

st.info("👉 Pour lancer l'application : `streamlit run app.py`")
