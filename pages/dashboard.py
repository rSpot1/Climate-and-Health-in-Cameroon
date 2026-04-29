"""
pages/dashboard.py — Tableau de bord : évolution temporelle des PM2.5 prédits par région
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.data import (
    load_city_profiles, load_global_stats, load_risk_table,
    load_model, load_features, fetch_realtime_meteo,
    build_feature_row, predict_pm25, get_region_city_enc,
    pm25_level, pm25_color,
)
from utils.charts import (
    regional_timeseries, region_month_heatmap,
    stagnation_scatter, pm25_gauge_dashboard, city_bar,
)


def _generate_predicted_ts(risk_df: pd.DataFrame, cities_df: pd.DataFrame,
                             model, features: list[str]) -> pd.DataFrame:
    """
    Génère une série temporelle mensuelle en utilisant les PM2.5 de risk_table
    modulés par la saisonnalité réelle du modèle (facteurs calibrés sur le notebook).
    """
    season_factor = {
        1:1.42, 2:1.50, 3:1.35, 4:0.93, 5:0.75, 6:0.70,
        7:0.65, 8:0.65, 9:0.72, 10:0.85, 11:1.28, 12:1.40
    }
    month_names = ["Jan","Fév","Mar","Avr","Mai","Juin",
                   "Juil","Aoû","Sep","Oct","Nov","Déc"]
    regions = risk_df["region"].unique() if "region" in risk_df.columns else []
    records = []
    for reg in regions:
        reg_rows = risk_df[risk_df["region"] == reg]
        # Base = PM2.5 prédit moyen de la région (depuis risk_table)
        base_pm25 = float(reg_rows["pm25_moy"].mean()) if len(reg_rows) else 18.0
        for m in range(1, 13):
            pm25_m = max(base_pm25 * season_factor[m], 5.0)
            records.append({
                "date": pd.Timestamp(f"2024-{m:02d}-15"),
                "region": reg,
                "pm25_moy": pm25_m,
                "month_label": month_names[m - 1],
            })
    return pd.DataFrame(records)


def render():
    stats    = load_global_stats()
    risk_df  = load_risk_table()
    cities   = load_city_profiles()
    model    = load_model()
    features = load_features()

    st.markdown('<p class="page-title">Tableau de bord</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="page-subtitle">Évolution temporelle des PM2.5 prédits par région · ',
        unsafe_allow_html=True,
    )

    # ── Jauges PM2.5 prédit temps réel — villes clés ─────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">PM2.5 prédit aujourd\'hui — villes clés</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    key_cities = ["Maroua", "Garoua", "Ngaoundere", "Yaounde", "Douala"]
    key_cities = [c for c in key_cities if c in cities["city"].tolist()][:5]

    cols_gauge = st.columns(len(key_cities))
    for col, city_name in zip(cols_gauge, key_cities):
        with col:
            city_row = cities[cities["city"] == city_name].iloc[0]
            lat, lon = float(city_row["latitude"]), float(city_row["longitude"])
            region_enc, city_enc = get_region_city_enc(city_name, cities)
            meteo = fetch_realtime_meteo(lat, lon, days=1)
            if meteo is not None and len(meteo):
                feat = build_feature_row(meteo.iloc[0], lat, lon, region_enc, city_enc)
                pm25 = predict_pm25(model, feat, features)
            else:
                # Fallback sur risk_table si API indisponible
                rrow = risk_df[risk_df["city"] == city_name]
                pm25 = float(rrow["pm25_moy"].iloc[0]) if len(rrow) else 18.0
            st.plotly_chart(
                pm25_gauge_dashboard(pm25, city_name),
                width='stretch',
                config={"displayModeBar": False},
            )

    # ── Filtres ───────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Évolution régionale</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        regions_available = sorted(risk_df["region"].unique().tolist()) \
            if "region" in risk_df.columns else []
        selected_regions = st.multiselect(
            "Régions",
            options=regions_available,
            default=regions_available[:5] if len(regions_available) >= 5 else regions_available,
        )
    with col_f2:
        metric_choice = st.selectbox("Indicateur", ["PM2.5 moyen (µg/m³)", "Rapport au seuil OMS"])

    # ── Série temporelle prédite ──────────────────────────────────────────────
    df_ts = _generate_predicted_ts(risk_df, cities, model, features)
    if selected_regions:
        df_ts = df_ts[df_ts["region"].isin(selected_regions)]

    metric_col = "pm25_moy"
    if metric_choice == "Rapport au seuil OMS":
        df_ts = df_ts.copy()
        df_ts["pm25_ratio"] = df_ts["pm25_moy"] / stats["seuil_oms"]
        metric_col = "pm25_ratio"

    if len(df_ts):
        st.plotly_chart(
            regional_timeseries(df_ts, metric=metric_col, height=360),
            width='stretch',
            config={"displayModeBar": False},
        )
    else:
        st.info("Sélectionnez au moins une région.")

    # ── Heatmap saisonnière + scatter ─────────────────────────────────────────
    col_heat, col_sc = st.columns(2)

    with col_heat:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Saisonnalité PM2.5 prédit</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        df_heat = _generate_predicted_ts(risk_df, cities, model, features)
        if selected_regions:
            df_heat = df_heat[df_heat["region"].isin(selected_regions)]
        if len(df_heat):
            st.plotly_chart(
                region_month_heatmap(df_heat, height=300),
                width='stretch',
                config={"displayModeBar": False},
            )

    with col_sc:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Stagnation vs PM2.5 prédit</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        if len(risk_df) and "jours_stagnation" in risk_df.columns:
            st.plotly_chart(
                stagnation_scatter(risk_df, height=300),
                width='stretch',
                config={"displayModeBar": False},
            )

    # ── Prévisions 7j en temps réel pour une ville ────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Prévisions PM2.5 prédit — 7 jours</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    col_sel, _ = st.columns([2, 2])
    with col_sel:
        city_sel = st.selectbox(
            "Ville pour prévisions",
            cities["city"].tolist() if len(cities) else ["Maroua"],
            label_visibility="collapsed",
        )

    if city_sel and len(cities):
        city_row = cities[cities["city"] == city_sel].iloc[0]
        lat, lon = float(city_row["latitude"]), float(city_row["longitude"])
        region_enc, city_enc = get_region_city_enc(city_sel, cities)

        with st.spinner("Prédiction via modèle RF..."):
            meteo_7 = fetch_realtime_meteo(lat, lon, days=7)

        if meteo_7 is not None and len(meteo_7):
            dates_7, pm25_7 = [], []
            for _, row in meteo_7.iterrows():
                feat = build_feature_row(row, lat, lon, region_enc, city_enc)
                pm25_7.append(predict_pm25(model, feat, features))
                dates_7.append(row["time"])

            # Cards jours
            cols_fc = st.columns(len(dates_7))
            for i, (col, d, v) in enumerate(zip(cols_fc, dates_7, pm25_7)):
                color_i = pm25_color(v)
                lvl_i, _ = pm25_level(v)
                with col:
                    st.markdown(
                        f'<div class="forecast-day-card">'
                        f'<div class="forecast-day-label">{d.strftime("%a %d")}</div>'
                        f'<div class="forecast-day-value" style="color:{color_i}">{v:.1f}</div>'
                        f'<div class="forecast-day-sub">µg/m³</div>'
                        f'<div style="font-size:.62rem;color:{color_i};margin-top:2px">{lvl_i}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                '<div class="alert-banner alert-medium"> '
                '<div><div class="alert-title">API indisponible</div>'
                'Impossible de récupérer les données Open-Meteo.</div></div>',
                unsafe_allow_html=True,
            )

    # ── Table complète des PM2.5 prédits ──────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Table complète — PM2.5 prédit par ville</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    if len(risk_df):
        df_show = risk_df.sort_values("pm25_moy", ascending=False).copy()
        rows = []
        for _, r in df_show.iterrows():
            lvl, css = pm25_level(r["pm25_moy"])
            color = pm25_color(r["pm25_moy"])
            ratio = round(r["pm25_moy"] / stats["seuil_oms"], 1)
            rows.append(
                f'<tr>'
                f'<td class="bold">{r["city"]}</td>'
                f'<td style="color:#8b949e">{r["region"]}</td>'
                f'<td class="mono" style="color:{color}">{r["pm25_moy"]:.1f}</td>'
                f'<td class="mono">{r.get("pm25_p95", r["pm25_moy"]*1.4):.1f}</td>'
                f'<td class="mono">×{ratio}</td>'
                f'<td>{r.get("jours_stagnation","—")}</td>'
                f'<td><span class="badge badge-{css}">{lvl}</span></td>'
                f'</tr>'
            )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Ville</th><th>Région</th><th>PM2.5 moy.</th>'
            '<th>PM2.5 P95</th><th>Ratio OMS</th><th>Stagnation j/an</th><th>Niveau</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>',
            unsafe_allow_html=True,
        )


render()
