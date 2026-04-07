"""
pages/accueil.py — Carte de risque interactive + alertes temps réel
"""
from __future__ import annotations

import time
from datetime import datetime

import pytz
import pandas as pd
import streamlit as st

from utils.data import (
    fetch_realtime_meteo, load_city_profiles, load_global_stats,
    load_risk_table, pm25_level,
)
from utils.charts import risk_map, city_bar

# Définition du fuseau horaire local pour affichage de l'heure précise
tz = pytz.timezone('Africa/Douala') # Ou par exemple

def _alert_html(title: str, body: str, level: str) -> str:
    return (
        f'<div class="alert-banner alert-{level}">'
        f'<div><div class="alert-title">{title}</div>{body}</div>'
        f'</div>'
    )


def _metric(label: str, value: str, unit: str = "", delta: str = "", delta_up: bool = True) -> str:
    delta_class = "metric-delta-up" if delta_up else "metric-delta-down"
    delta_html = f'<span class="{delta_class}">{delta}</span>' if delta else ""
    return (
        f'<div class="metric-tile">'
        f'<span class="metric-label">{label}</span>'
        f'<span class="metric-value">{value}<span class="metric-unit"> {unit}</span></span>'
        f'{delta_html}</div>'
    )


def render():
    stats   = load_global_stats()
    risk_df = load_risk_table()
    cities  = load_city_profiles()

    # ── Header ──────────────────────────────────────────────────────────────
    col_title, col_live = st.columns([4, 1])
    with col_title:
        st.markdown('<p class="page-title">Surveillance de la qualité de l\'air</p>', unsafe_allow_html=True)
        # st.markdown(
        #     f'<p class="page-subtitle">Cameroun · {stats["n_villes"]} villes · '
        #     f'{stats["n_regions"]} régions · '
        #     f'{stats["periode_debut"]} → {stats["periode_fin"]}</p>',
        #     unsafe_allow_html=True,
        # )
    with col_live:
        st.markdown(
            f'<div style="text-align:right;padding-top:1rem;">'
            f'<span class="live-dot"></span>'
            f'<span style="font-size:.75rem;color:#8b949e;">Open-Meteo API</span><br>'
            f'<span style="font-family:\'IBM Plex Mono\';font-size:.7rem;color:#6e7681;">'
            f'{datetime.now(tz).strftime("%H:%M · %d %b %Y")}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Alertes temps réel ────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Alertes temps réel</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    # Générer alertes depuis la table de risque
    critical_cities = risk_df[risk_df["pm25_moy"] > 25]["city"].tolist() if len(risk_df) else []
    high_cities     = risk_df[(risk_df["pm25_moy"] > 20) & (risk_df["pm25_moy"] <= 25)]["city"].tolist() if len(risk_df) else []

    now_month = datetime.now().month
    harmattan_active = now_month in [11, 12, 1, 2]

    if harmattan_active:
        st.markdown(_alert_html(
            "Saison Harmattan active",
            "Les vents du Nord chargés de poussières sahéliennes augmentent significativement "
            "les concentrations de PM2.5 dans les régions Extrême-Nord et Nord. "
            "Recommandation : limiter les activités extérieures prolongées.",
            "critical",
        ), unsafe_allow_html=True)

    if critical_cities:
        st.markdown(_alert_html(
            f"Niveau critique — {len(critical_cities)} ville(s)",
            f"PM2.5 > 25 µg/m³ : {', '.join(critical_cities[:5])}. "
            "Groupes vulnérables (enfants, personnes âgées, asthmatiques) : rester en intérieur.",
            "high",
        ), unsafe_allow_html=True)

    if high_cities:
        st.markdown(_alert_html(
            f"Niveau élevé — {len(high_cities)} ville(s)",
            f"PM2.5 entre 20 et 25 µg/m³ : {', '.join(high_cities[:4])}. Vigilance recommandée.",
            "medium",
        ), unsafe_allow_html=True)

    if not harmattan_active and not critical_cities and not high_cities:
        st.markdown(_alert_html(
            "Qualité de l'air satisfaisante",
            "Aucune ville ne dépasse le seuil critique (25 µg/m³) en ce moment.",
            "info",
        ), unsafe_allow_html=True)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Indicateurs nationaux</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    pm25_moy = stats["pm25_national_moy"]
    pm25_p95 = stats["pm25_national_p95"]
    oms_ratio = round(pm25_moy / stats["seuil_oms"], 1)

    with c1:
        st.markdown(_metric("PM2.5 national moyen", f"{pm25_moy:.1f}", "µg/m³",
                             f"× {oms_ratio} seuil OMS", delta_up=True), unsafe_allow_html=True)
    with c2:
        st.markdown(_metric("PM2.5 P95 national", f"{pm25_p95:.1f}", "µg/m³"), unsafe_allow_html=True)
    with c3:
        st.markdown(_metric("Villes en zone critique",
                             str(len(risk_df[risk_df["pm25_moy"] > 25])) if len(risk_df) else "—",
                             f"/ {stats['n_villes']}"), unsafe_allow_html=True)
    with c4:
        st.markdown(_metric("Période couverte",
                             str(stats.get("n_observations", 87240) // 1000) + "K",
                             "observations"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Carte + classement ────────────────────────────────────────────────────
    col_map, col_rank = st.columns([3, 1])

    with col_map:
        st.markdown('<p class="section-label">Carte de risque PM2.5 par ville</p>', unsafe_allow_html=True)
        if len(risk_df):
            st.plotly_chart(risk_map(risk_df), width='stretch', config={"displayModeBar": False})
        else:
            st.info("Données cartographiques indisponibles.")

    with col_rank:
        st.markdown('<p class="section-label">Classement des villes</p>', unsafe_allow_html=True)
        if len(risk_df):
            top = risk_df.sort_values("pm25_moy", ascending=False).head(10).reset_index(drop=True)
            rows = []
            for _, r in top.iterrows():
                lvl, css = pm25_level(r["pm25_moy"])
                rows.append(
                    f'<tr>'
                    f'<td class="bold">{r["city"]}</td>'
                    f'<td class="mono">{r["pm25_moy"]:.1f}</td>'
                    f'<td><span class="badge badge-{css}">{lvl[:6]}</span></td>'
                    f'</tr>'
                )
            table_html = (
                '<table class="data-table">'
                '<thead><tr><th>Ville</th><th>µg/m³</th><th>Niveau</th></tr></thead>'
                '<tbody>' + "".join(rows) + '</tbody></table>'
            )
            st.markdown(table_html, unsafe_allow_html=True)

    # ── Bar chart régions ─────────────────────────────────────────────────────
    if len(risk_df) and "region" in risk_df.columns:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">PM2.5 moyen par ville</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            city_bar(risk_df.head(20), title=""),
            width='stretch',
            config={"displayModeBar": False},
        )

    # ── Données temps réel — sélection ville ─────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Conditions météo actuelles</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    col_sel, col_btn = st.columns([2, 1])
    with col_sel:
        city_choice = st.selectbox(
            "Sélectionner une ville",
            cities["city"].tolist() if len(cities) else ["Maroua"],
            label_visibility="visible",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("Actualiser les données", width='stretch')

    if city_choice and len(cities):
        city_row = cities[cities["city"] == city_choice].iloc[0]
        lat, lon = float(city_row["latitude"]), float(city_row["longitude"])

        with st.spinner("Interrogation de l'API Open-Meteo..."):
            meteo = fetch_realtime_meteo(lat, lon, days=3)

        if meteo is not None and len(meteo):
            today = meteo.iloc[0]
            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                st.markdown(_metric("Température", f"{today.get('temperature_2m_mean', '—'):.0f}", "°C"), unsafe_allow_html=True)
            with mc2:
                precip = today.get('precipitation_sum', 0) or 0
                st.markdown(_metric("Précipitations", f"{precip:.1f}", "mm"), unsafe_allow_html=True)
            with mc3:
                wind = today.get('wind_speed_10m_max', 0) or 0
                st.markdown(_metric("Vent max", f"{wind:.0f}", "km/h"), unsafe_allow_html=True)
            with mc4:
                rad = today.get('shortwave_radiation_sum', 0) or 0
                st.markdown(_metric("Radiation", f"{rad:.0f}", "MJ/m²"), unsafe_allow_html=True)
            with mc5:
                et0 = today.get('et0_fao_evapotranspiration', 0) or 0
                st.markdown(_metric("ET0", f"{et0:.1f}", "mm"), unsafe_allow_html=True)
        else:
            st.markdown(
                _alert_html("API indisponible",
                             "Impossible de contacter Open-Meteo. Vérifiez votre connexion.",
                             "medium"),
                unsafe_allow_html=True,
            )

# ── Point d'entrée Streamlit multi-pages ──
render()
