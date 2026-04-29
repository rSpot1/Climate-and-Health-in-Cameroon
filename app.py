"""
AirQual Cameroun — Application web de surveillance prédictive de la qualité de l'air
Point d'entrée principal — navigation multi-pages native Streamlit
"""
import streamlit as st

st.set_page_config(
    page_title="AirQual CM",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "AirQual CM — Surveillance prédictive de la qualité de l'air au Cameroun.\n"
            "AlphaInfera"
        ),
    },
)

# CSS global
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar branding
st.sidebar.markdown(
    '<div class="sidebar-brand">'
    '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
    '<div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#f0a500,#388bfd);'
    'display:flex;align-items:center;justify-content:center;font-size:16px"></div>'
    '<div>'
    '<div class="sidebar-brand-title">AirQual CM</div>'
    '<div class="sidebar-brand-sub">AlphaInfera</div>'
    '</div></div>'
    '<div style="font-size:.68rem;color:#6e7681;font-family:\'IBM Plex Mono\',monospace;'
    'border-top:1px solid #21262d;padding-top:8px;margin-top:4px">'
    '</div></div>',
    unsafe_allow_html=True,
)

pg = st.navigation([
    st.Page("pages/accueil.py",    title="Accueil",          default=True),
    st.Page("pages/predicteur.py", title="Prédicteur"),
    st.Page("pages/dashboard.py",  title="Tableau de bord"),
    st.Page("pages/spatial.py",    title="Analyse spatiale"),
    st.Page("pages/apropos.py",    title="À propos"),
])
pg.run()
