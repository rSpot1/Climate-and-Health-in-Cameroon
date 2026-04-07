"""
pages/predicteur.py — Formulaire météo → prédiction PM2.5 temps réel
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from utils.data import (
    build_feature_row, fetch_realtime_meteo, load_city_profiles,
    load_features, load_global_stats, load_model, pm25_level, predict_pm25,
)
from utils.charts import pm25_gauge


def _bar(label: str, value: float, max_val: float, color: str) -> str:
    pct = min(value / max(max_val, 1) * 100, 100)
    return (
        f'<div class="pm25-bar-wrap">'
        f'<div class="pm25-bar-label"><span>{label}</span><span style="font-family:\'IBM Plex Mono\'">{value:.2f}</span></div>'
        f'<div class="pm25-bar-track"><div class="pm25-bar-fill" style="width:{pct:.1f}%;background:{color};"></div></div>'
        f'</div>'
    )


def render():
    model    = load_model()
    features = load_features()
    stats    = load_global_stats()
    cities   = load_city_profiles()

    st.markdown('<p class="page-title">Prédicteur PM2.5</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Saisissez les conditions météorologiques ou chargez '
        'automatiquement les données temps réel via API pour obtenir une prédiction PM2.5.</p>',
        unsafe_allow_html=True,
    )

    # ── Sélection ville + chargement API ─────────────────────────────────────
    col_city, col_api = st.columns([2, 1])
    with col_city:
        city_choice = st.selectbox(
            "Ville de référence (initialise les valeurs par défaut)",
            ["— Saisie manuelle —"] + (cities["city"].tolist() if len(cities) else []),
        )
    with col_api:
        st.markdown("<br>", unsafe_allow_html=True)
        load_api = st.button("Charger depuis API Open-Meteo", width='stretch')

    # Récupération données API si demandé
    api_data = None
    lat_default, lon_default = 3.87, 11.52
    region_enc_default, city_enc_default = 2, 0

    if city_choice != "— Saisie manuelle —" and len(cities):
        row = cities[cities["city"] == city_choice].iloc[0]
        lat_default  = float(row["latitude"])
        lon_default  = float(row["longitude"])
        city_list    = cities["city"].tolist()
        city_enc_default = city_list.index(city_choice) if city_choice in city_list else 0

    if load_api and city_choice != "— Saisie manuelle —":
        with st.spinner("Appel API Open-Meteo..."):
            df_api = fetch_realtime_meteo(lat_default, lon_default, days=1)
        if df_api is not None and len(df_api):
            api_data = df_api.iloc[0]
            st.markdown(
                '<div class="alert-banner alert-info">'
                '<div><div class="alert-title">Données chargées</div>'
                f'Open-Meteo · {city_choice} · {datetime.now().strftime("%H:%M")}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="alert-banner alert-medium"><div>'
                '<div class="alert-title">API indisponible</div>'
                'Les valeurs par défaut ont été utilisées.</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Formulaire météo ──────────────────────────────────────────────────────
    st.markdown('<p class="section-label">Paramètres météorologiques</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    def get(key, default):
        if api_data is not None and key in api_data.index:
            v = api_data[key]
            return float(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else default
        if city_choice != "— Saisie manuelle —" and len(cities):
            mapping = {
                "temperature_2m_mean": "temp_moy",
                "precipitation_sum":   "precip_moy",
                "wind_speed_10m_max":  "vent_moy",
                "shortwave_radiation_sum": "radiation_moy",
                "et0_fao_evapotranspiration": "et0_moy",
            }
            if key in mapping:
                col = mapping[key]
                if col in cities.columns:
                    return float(cities[cities["city"] == city_choice].iloc[0][col])
        return default

    with col1:
        t_mean = st.slider("Température moyenne (°C)",  10.0, 45.0, get("temperature_2m_mean", 26.0), 0.5)
        t_max  = st.slider("Température maximale (°C)", 15.0, 50.0, get("temperature_2m_max", 32.0), 0.5)
        t_min  = st.slider("Température minimale (°C)", 5.0,  35.0, get("temperature_2m_min", 20.0), 0.5)
        precip = st.slider("Précipitations (mm)",       0.0, 300.0, get("precipitation_sum", 0.5), 0.5)

    with col2:
        wind   = st.slider("Vent max (km/h)",           0.0,  60.0, get("wind_speed_10m_max", 12.0), 0.5)
        gusts  = st.slider("Rafales max (km/h)",        0.0,  80.0, get("wind_gusts_10m_max", 18.0), 0.5)
        rad    = st.slider("Radiation solaire (MJ/m²)", 0.0,  30.0, get("shortwave_radiation_sum", 18.0), 0.5)
        et0    = st.slider("Évapotranspiration ET0 (mm)", 0.0, 15.0, get("et0_fao_evapotranspiration", 4.0), 0.1)

    with col3:
        sun    = st.slider("Durée d'ensoleillement (h)",  0.0, 14.0, 8.0, 0.5)
        day    = st.slider("Durée du jour (h)",           10.0, 13.5, 12.0, 0.5)
        lat    = st.number_input("Latitude",  min_value=-5.0, max_value=15.0, value=lat_default, step=0.1)
        lon    = st.number_input("Longitude", min_value=8.0,  max_value=17.0, value=lon_default, step=0.1)

    # ── Mois et saison ────────────────────────────────────────────────────────
    month_names = ["Janvier","Février","Mars","Avril","Mai","Juin",
                   "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    month = st.select_slider("Mois", options=list(range(1, 13)),
                              format_func=lambda m: month_names[m-1],
                              value=datetime.now().month)
    is_dry = int(month in [11, 12, 1, 2, 3])

    st.markdown("---")

    # ── Prédiction ────────────────────────────────────────────────────────────
    col_pred, col_detail = st.columns([1, 1])

    sun_sec = sun * 3600
    day_sec = day * 3600

    feat_row = build_feature_row(
        pd.Series({
            "time": datetime(2025, month, 15),
            "temperature_2m_mean":        t_mean,
            "temperature_2m_max":         t_max,
            "temperature_2m_min":         t_min,
            "precipitation_sum":          precip,
            "wind_speed_10m_max":         wind,
            "wind_gusts_10m_max":         gusts,
            "shortwave_radiation_sum":    rad,
            "et0_fao_evapotranspiration": et0,
            "sunshine_duration":          sun_sec,
            "daylight_duration":          day_sec,
        }),
        lat=lat, lon=lon,
        region_enc=region_enc_default,
        city_enc=city_enc_default,
    )

    pm25_pred = predict_pm25(model, feat_row, features)
    level_label, level_css = pm25_level(pm25_pred)

    with col_pred:
        st.plotly_chart(pm25_gauge(pm25_pred), width='stretch',
                        config={"displayModeBar": False})
        oms_ratio = pm25_pred / stats["seuil_oms"]
        badge_html = f'<span class="badge badge-{level_css}">{level_label}</span>'
        st.markdown(
            f'<div style="text-align:center;margin-top:.5rem;">'
            f'{badge_html}'
            f'<span style="font-size:.78rem;color:#8b949e;margin-left:.75rem;">'
            f'× {oms_ratio:.2f} seuil OMS (15 µg/m³)</span></div>',
            unsafe_allow_html=True,
        )

    with col_detail:
        st.markdown('<p class="section-label">Contribution des facteurs</p>', unsafe_allow_html=True)

        contributions = {
            "Température":      t_mean * 0.35,
            "Radiation solaire": rad * 0.25,
            "Évapotranspiration": et0 * 0.20,
            "Stagnation (vent)": 8.0 * int(wind < 5),
            "Absence pluie":    5.0 * int(precip < 0.1),
            "Saison sèche":     4.0 * is_dry,
        }
        max_contrib = max(contributions.values()) if contributions else 1
        colors = ["#f0a500", "#388bfd", "#3fb950", "#da3633", "#f0883e", "#d29922"]

        for (name, val), color in zip(contributions.items(), colors):
            st.markdown(_bar(name, val, max_contrib, color), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Recommandations
        if level_css in ("critical", "high"):
            st.markdown(
                '<div class="alert-banner alert-critical"><div>'
                '<div class="alert-title">Recommandations sanitaires</div>'
                'Évitez les activités physiques extérieures. Fermez les fenêtres. '
                'Portez un masque FFP2 en cas de sortie nécessaire.</div></div>',
                unsafe_allow_html=True,
            )
        elif level_css == "medium":
            st.markdown(
                '<div class="alert-banner alert-medium"><div>'
                '<div class="alert-title">Vigilance modérée</div>'
                'Groupes vulnérables : limitez les sorties prolongées. '
                'Surveillez l\'évolution au cours de la journée.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="alert-banner alert-info"><div>'
                '<div class="alert-title">Qualité de l\'air acceptable</div>'
                'Les conditions actuelles sont favorables. Seuil OMS respecté.</div></div>',
                unsafe_allow_html=True,
            )

    # ── Prévision 7 jours ─────────────────────────────────────────────────────
    if city_choice != "— Saisie manuelle —":
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Prévision 7 jours</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        with st.spinner("Chargement des prévisions..."):
            df7 = fetch_realtime_meteo(lat, lon, days=7)

        if df7 is not None and len(df7):
            preds_7 = []
            for _, row7 in df7.iterrows():
                fr = build_feature_row(row7, lat=lat, lon=lon,
                                        region_enc=region_enc_default,
                                        city_enc=city_enc_default)
                preds_7.append({
                    "date": row7["time"].strftime("%a %d %b") if hasattr(row7["time"], "strftime") else str(row7["time"]),
                    "pm25": predict_pm25(model, fr, features),
                })

            rows_html = []
            for p in preds_7:
                lbl, css = pm25_level(p["pm25"])
                rows_html.append(
                    f'<tr><td class="bold">{p["date"]}</td>'
                    f'<td class="mono">{p["pm25"]:.2f}</td>'
                    f'<td><span class="badge badge-{css}">{lbl}</span></td></tr>'
                )
            st.markdown(
                '<table class="data-table"><thead><tr>'
                '<th>Date</th><th>PM2.5 (µg/m³)</th><th>Niveau</th>'
                '</tr></thead><tbody>' + "".join(rows_html) + '</tbody></table>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Prévisions indisponibles (API hors ligne).")

# ── Point d'entrée Streamlit multi-pages ──
render()
