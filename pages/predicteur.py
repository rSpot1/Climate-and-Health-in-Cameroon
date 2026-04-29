"""
pages/predicteur.py — Prédicteur PM2.5 avec modèle AlphaInfera + données Open-Meteo
"""
from __future__ import annotations
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st

from utils.data import (
    build_feature_row, fetch_realtime_meteo, load_city_profiles,
    load_features, load_global_stats, load_model, pm25_level,
    pm25_color, predict_pm25, oms_ratio,
)
from utils.charts import pm25_gauge, forecast_line, meteo_lines


def _bar(label, value, max_val, color):
    pct = min(value / max(max_val, 1) * 100, 100)
    return (
        f'<div class="pm25-bar-wrap">'
        f'<div class="pm25-bar-label"><span>{label}</span>'
        f'<span style="font-family:\'IBM Plex Mono\'">{value:.2f}</span></div>'
        f'<div class="pm25-bar-track">'
        f'<div class="pm25-bar-fill" style="width:{pct:.1f}%;background:{color}"></div>'
        f'</div></div>'
    )


def render():
    model    = load_model()
    features = load_features()
    stats    = load_global_stats()
    cities   = load_city_profiles()

    st.markdown('<p class="page-title">Prédicteur PM2.5</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Sélectionnez une ville ou entrez des paramètres météo manuellement. '
        'Les données Open-Meteo alimentent le modèle</b> '
        'pour calculer le PM2.5 prédit.</p>',
        unsafe_allow_html=True,
    )

    # ── Sélection ville ───────────────────────────────────────────────────────
    col_city, col_api = st.columns([3, 1])
    with col_city:
        city_list = ["— Saisie manuelle —"] + (cities["city"].tolist() if len(cities) else [])
        city_choice = st.selectbox("Ville", city_list, label_visibility="collapsed")
    with col_api:
        load_api = st.button("📡 Charger Open-Meteo", width='stretch')

    lat_def, lon_def = 10.60, 14.33
    region_enc_def, city_enc_def = 3, 0

    if city_choice != "— Saisie manuelle —" and len(cities):
        row = cities[cities["city"] == city_choice].iloc[0]
        lat_def, lon_def = float(row["latitude"]), float(row["longitude"])
        city_list_raw = cities["city"].tolist()
        city_enc_def  = city_list_raw.index(city_choice) if city_choice in city_list_raw else 0
        region_enc_def = sorted(cities["region"].unique().tolist()).index(row["region"]) \
            if row["region"] in sorted(cities["region"].unique().tolist()) else 0

    api_data = None
    if load_api and city_choice != "— Saisie manuelle —":
        with st.spinner("Appel Open-Meteo..."):
            df_api = fetch_realtime_meteo(lat_def, lon_def, days=7)
        if df_api is not None and len(df_api):
            api_data = df_api.iloc[0]
            st.markdown(
                f'<div class="alert-banner alert-info">📡 '
                f'<div><div class="alert-title">Données chargées depuis Open-Meteo</div>'
                f'{city_choice} · {datetime.now().strftime("%d %b %Y %H:%M")}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="alert-banner alert-medium"> '
                '<div><div class="alert-title">API indisponible</div>'
                'Valeurs par défaut utilisées.</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Formulaire météo ──────────────────────────────────────────────────────
    st.markdown('<p class="section-label">Paramètres météorologiques</p>', unsafe_allow_html=True)

    def get_val(key, default, city_mapping=None):
        if api_data is not None and key in api_data.index:
            v = api_data[key]
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                return float(v)
        if city_mapping and city_choice != "— Saisie manuelle —" and len(cities):
            row = cities[cities["city"] == city_choice].iloc[0]
            col = city_mapping.get(key)
            if col and col in row.index:
                return float(row[col])
        return default

    col1, col2, col3 = st.columns(3)
    with col1:
        t_mean = st.number_input(" Temp. moyenne (°C)", value=get_val("temperature_2m_mean", 28.0, {"temperature_2m_mean":"temp_moy"}), step=0.5)
        t_max  = st.number_input(" Temp. max (°C)",     value=get_val("temperature_2m_max",  34.0, {"temperature_2m_max":"temp_max"}), step=0.5)
        t_min  = st.number_input(" Temp. min (°C)",     value=get_val("temperature_2m_min",  22.0, {"temperature_2m_min":"temp_min"}), step=0.5)
    with col2:
        precip = st.number_input(" Précipitations (mm)", value=get_val("precipitation_sum", 0.0, {"precipitation_sum":"precip_moy"}), step=0.1, min_value=0.0)
        wind   = st.number_input(" Vent max (km/h)",     value=get_val("wind_speed_10m_max", 12.0, {"wind_speed_10m_max":"vent_moy"}), step=0.5, min_value=0.0)
        gusts  = st.number_input(" Rafales (km/h)",      value=get_val("wind_gusts_10m_max", 20.0), step=0.5, min_value=0.0)
    with col3:
        rad    = st.number_input(" Radiation (MJ/m²)",   value=get_val("shortwave_radiation_sum", 20.0, {"shortwave_radiation_sum":"radiation_moy"}), step=0.5, min_value=0.0)
        et0    = st.number_input(" ET0 FAO (mm/j)",      value=get_val("et0_fao_evapotranspiration", 4.5, {"et0_fao_evapotranspiration":"et0_moy"}), step=0.1, min_value=0.0)
        month  = st.slider(" Mois", 1, 12, datetime.now().month)

    # ── Prédiction ────────────────────────────────────────────────────────────
    st.markdown("---")

    if st.button(" Calculer la prédiction PM2.5", width='stretch', type="primary"):
        sun_ratio = 0.65
        feat_row = build_feature_row(
            pd.Series({
                "time": pd.Timestamp(f"2024-{month:02d}-15"),
                "temperature_2m_mean": t_mean,
                "temperature_2m_max": t_max,
                "temperature_2m_min": t_min,
                "precipitation_sum": precip,
                "wind_speed_10m_max": wind,
                "wind_gusts_10m_max": gusts,
                "shortwave_radiation_sum": rad,
                "et0_fao_evapotranspiration": et0,
                "sunshine_duration": sun_ratio * 44000,
                "daylight_duration": 44000,
            }),
            lat=lat_def, lon=lon_def,
            region_enc=region_enc_def, city_enc=city_enc_def,
        )

        pm25_pred = predict_pm25(model, feat_row, features)
        lvl_label, lvl_css = pm25_level(pm25_pred)
        color = pm25_color(pm25_pred)
        ratio = oms_ratio(pm25_pred)

        col_gauge, col_details = st.columns([1, 2])
        with col_gauge:
            label = city_choice if city_choice != "— Saisie manuelle —" else "Saisie manuelle"
            st.plotly_chart(pm25_gauge(pm25_pred, label),
                            width='stretch', config={"displayModeBar": False})

        with col_details:
            st.markdown(
                f'<div class="card card-accent" style="margin-top:8px">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">'
                f'<div style="font-size:2rem;font-weight:700;font-family:\'IBM Plex Mono\';color:{color}">'
                f'{pm25_pred:.2f} <span style="font-size:1rem;color:#8b949e">µg/m³</span></div>'
                f'<span class="badge badge-{lvl_css}">{lvl_label}</span></div>'
                + _bar("vs. seuil OMS (15 µg/m³)", min(pm25_pred, 45), 45, color)
                + _bar("vs. P95 national (" + f'{stats["pm25_national_p95"]:.0f} µg/m³)', min(pm25_pred, 45), 45, "#388bfd")
                + f'<div style="margin-top:12px;font-size:.78rem;color:#8b949e">'
                f'<b style="color:#e6edf3">Rapport au seuil OMS :</b> '
                f'<span style="color:{color};font-family:\'IBM Plex Mono\'">×{ratio}</span> '
                f'{"⚠️ Dépassement" if pm25_pred > 15 else " Conforme"}</div>'
                + f'<div style="margin-top:8px;font-size:.72rem;color:#6e7681">'
                f'🤖 Modèle : AlphaInfera RF ({"actif" if model is not None else "proxy calibré"})'
                f' · MAE={stats["best_model_mae"]:.4f} · R²={stats["best_model_r2"]:.4f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Recommandation santé
            reco = {
                "Bon":        ("✅", "Qualité de l'air satisfaisante. Activités extérieures sans restriction.", "info"),
                "Modéré":     ("🟡", "Qualité acceptable. Personnes sensibles : limiter les efforts intenses.", "medium"),
                "Élevé":      ("🟠", "Groupes vulnérables (enfants, âgés, asthmatiques) : réduire les sorties.", "high"),
                "Très élevé": ("🔴", "Tous : limiter les activités extérieures. Port de masque FFP2 recommandé.", "critical"),
            }.get(lvl_label, ("⚪", "", "info"))
            st.markdown(
                f'<div class="alert-banner alert-{reco[2]}" style="margin-top:12px">'
                f'<span style="font-size:1.1rem">{reco[0]}</span>'
                f'<div><div class="alert-title">Recommandation santé</div>'
                f'<span style="font-size:.82rem;color:#8b949e">{reco[1]}</span></div></div>',
                unsafe_allow_html=True,
            )

    # ── Prévisions 7j si ville sélectionnée ──────────────────────────────────
    if city_choice != "— Saisie manuelle —" and len(cities):
        st.markdown("---")
        st.markdown(
            '<p class="section-label">Prévisions PM2.5 — 7 jours (modèle)</p>',
            unsafe_allow_html=True,
        )
        with st.spinner("Calcul des prévisions..."):
            meteo_7 = fetch_realtime_meteo(lat_def, lon_def, days=7)
        if meteo_7 is not None and len(meteo_7):
            dates, pm25s = [], []
            temp_max_l, temp_min_l, wind_l = [], [], []
            for _, row in meteo_7.iterrows():
                feat = build_feature_row(row, lat_def, lon_def, region_enc_def, city_enc_def)
                pm25s.append(predict_pm25(model, feat, features))
                dates.append(row["time"])
                temp_max_l.append(row.get("temperature_2m_max", 30) or 30)
                temp_min_l.append(row.get("temperature_2m_min", 20) or 20)
                wind_l.append(row.get("wind_speed_10m_max", 12) or 12)

            col_fc, col_mt = st.columns(2)
            with col_fc:
                st.plotly_chart(forecast_line(dates, pm25s, city_choice),
                                width='stretch', config={"displayModeBar": False})
            with col_mt:
                st.plotly_chart(meteo_lines(dates, temp_max_l, temp_min_l, wind_l),
                                width='stretch', config={"displayModeBar": False})


render()
