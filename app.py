"""
AirQual Cameroun — Application de surveillance de la qualité de l'air
Point d'entrée principal — navigation multi-pages native Streamlit
"""
import streamlit as st

st.set_page_config(
    page_title="AirQual Cameroun",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "AirQual Cameroun — Surveillance prédictive de la qualité de l'air.\n"
            "Hackathon IndabaX Cameroon 2026."
        ),
    },
)

# Injection CSS globale
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Navigation multi-pages native ────────────────────────────────────────────
# st.navigation crée des URLs /accueil, /predicteur, etc.
# et gère automatiquement le sidebar sans radio manuel.
pg = st.navigation([
    st.Page("pages/accueil.py",   title="Accueil",          default=True),
    st.Page("pages/predicteur.py",title="Prédicteur",       ),
    st.Page("pages/dashboard.py", title="Tableau de bord",  ),
    st.Page("pages/spatial.py",   title="Analyse spatiale",  ),
    st.Page("pages/apropos.py",   title="À propos",         ),
])
pg.run()
