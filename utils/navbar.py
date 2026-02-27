"""
Composant Navbar réutilisable pour AnalogLab
"""
import streamlit as st


def render_navbar(active_page=None):
    """
    Affiche la navbar horizontale.
    Args:
        active_page: "home", "platform", "digital", "recommendations", "about", "contact", "inbox"
    """

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{ display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        div[data-testid="collapsedControl"] {{ display: none !important; }}
        [data-testid="stSidebarNav"] {{ display: none !important; }}

        .analoglab-navbar {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
            padding: 1.2rem 3rem;
            background: rgba(6,10,20,0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255,255,255,0.06);
            margin: -1rem -1rem 2rem -1rem;
            position: relative;
            z-index: 1000;
        }}

        .navbar-logo {{
            font-size: 1.4em;
            font-weight: 900;
            letter-spacing: -1px;
            background: linear-gradient(135deg, #00FFB2 20%, #00E6A1 80%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-right: 1rem;
            flex-shrink: 0;
            text-decoration: none !important;
            display: inline-block;
            cursor: pointer;
        }}

        .navbar-links {{
            display: flex;
            gap: 0.5rem;
            flex: 1;
            align-items: center;
        }}

        .navbar-link {{
            color: #9CA3AF;
            font-weight: 600;
            font-size: 0.92em;
            padding: 8px 16px;
            border-radius: 8px;
            transition: all 0.2s ease;
            text-decoration: none !important;
            display: inline-block;
            font-family: 'Inter', sans-serif;
            border: none;
            border-bottom: none !important;
            background: transparent;
            cursor: pointer;
        }}

        .navbar-link:hover {{
            color: #00FFB2 !important;
            background: rgba(0,255,178,0.07);
            text-decoration: none !important;
            border-bottom: none !important;
        }}

        .navbar-link.active {{
            color: #00FFB2 !important;
            font-weight: 700;
            pointer-events: none;
            text-decoration: none !important;
            border-bottom: none !important;
        }}

        .navbar-spacer {{
            flex: 1;
        }}

        .navbar-cta {{
            background: #00FFB2 !important;
            color: #060A14 !important;
            font-weight: 800;
            padding: 10px 24px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none !important;
            display: inline-block;
            font-family: 'Inter', sans-serif;
            font-size: 0.88em;
            border-bottom: none !important;
        }}

        .navbar-cta:hover {{
            background: #00E6A1 !important;
            transform: translateY(-2px);
        }}
        </style>

        <div class="analoglab-navbar">
            <a href="/" target="_self" class="navbar-logo">AnalogLab</a>
            <div class="navbar-links">
                <a href="/" target="_self" class="navbar-link {'active' if active_page == 'home' else ''}">Accueil</a>
                <a href="/agent_interface" target="_self" class="navbar-link {'active' if active_page == 'platform' else ''}">Analogique</a>
                <a href="/digital_hls" target="_self" class="navbar-link {'active' if active_page == 'digital' else ''}">Numérique</a>
                <a href="/recommendations" target="_self" class="navbar-link {'active' if active_page == 'recommendations' else ''}">Idées</a>
                <a href="/about" target="_self" class="navbar-link {'active' if active_page == 'about' else ''}">À Propos</a>
            </div>
            <div class="navbar-spacer"></div>
            <a href="/inbox" target="_self" class="navbar-link {'active' if active_page == 'inbox' else ''}">Inbox</a>
            <a href="/contact" target="_self" class="navbar-link {'active' if active_page == 'contact' else ''}">Contact</a>
            <a href="/agent_interface" target="_self" class="navbar-cta">Commencer</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
