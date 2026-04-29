"""
pages/spatial.py — Analyse spatiale des PM2.5 prédits par le modèle AlphaInfera
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data import (
    load_city_profiles, load_risk_table, load_global_stats,
    load_model, load_features, fetch_realtime_meteo,
    build_feature_row, predict_pm25, get_region_city_enc,
    pm25_level, pm25_color,
)
from utils.charts import risk_map, city_bar, stagnation_scatter


def render():
    risk_df  = load_risk_table()
    cities   = load_city_profiles()
    stats    = load_global_stats()
    model    = load_model()
    features = load_features()

    st.markdown('<p class="page-title">Analyse spatiale</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Comparaison des zones à risque, profils climatiques '
        'et PM2.5 prédits par ville. Toutes les valeurs sont issues du modèle ',
        unsafe_allow_html=True,
    )

    # ── Filtres ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        nivs = ["Tous"] + sorted(risk_df["niveau_risque"].unique().tolist()) \
            if "niveau_risque" in risk_df.columns else ["Tous"]
        niv_filter = st.selectbox("Niveau de risque", nivs)
    with col_f2:
        regions_all = ["Toutes"] + sorted(risk_df["region"].unique().tolist()) \
            if "region" in risk_df.columns else ["Toutes"]
        region_filter = st.selectbox("Région", regions_all)
    with col_f3:
        sort_col = st.selectbox("Trier par", ["PM2.5 moyen", "PM2.5 P95", "Jours de stagnation"])

    sort_map = {
        "PM2.5 moyen":          "pm25_moy",
        "PM2.5 P95":            "pm25_p95",
        "Jours de stagnation":  "jours_stagnation",
    }
    s_col = sort_map[sort_col]

    df_filtered = risk_df.copy()
    if niv_filter != "Tous" and "niveau_risque" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["niveau_risque"] == niv_filter]
    if region_filter != "Toutes" and "region" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["region"] == region_filter]
    if s_col in df_filtered.columns:
        df_filtered = df_filtered.sort_values(s_col, ascending=False)

    st.markdown("---")

    # ── Carte PM2.5 prédits ───────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Carte des PM2.5 prédits</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )
    if len(df_filtered):
        st.plotly_chart(
            risk_map(df_filtered, height=500),
            width='stretch',
            config={"displayModeBar": False},
        )
        st.markdown(
            '<div style="font-size:.7rem;color:#6e7681;text-align:right;margin-top:-8px">'
            ' Valeurs issues du modèle</div>',
            unsafe_allow_html=True,
        )

    # ── Bar + Scatter ─────────────────────────────────────────────────────────
    col_bar, col_sc = st.columns(2)

    with col_bar:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">PM2.5 prédit — top 20 villes</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        if len(df_filtered):
            st.plotly_chart(
                city_bar(df_filtered.head(20), height=380),
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
        if len(df_filtered) and "jours_stagnation" in df_filtered.columns:
            st.plotly_chart(
                stagnation_scatter(df_filtered, height=380),
                width='stretch',
                config={"displayModeBar": False},
            )

    # ── Comparaison deux villes — PM2.5 prédit en temps réel ──────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Comparaison de villes — PM2.5 prédit temps réel</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    city_list = cities["city"].tolist() if len(cities) else []
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        city_a = st.selectbox("Ville A", city_list,
                               index=city_list.index("Maroua") if "Maroua" in city_list else 0)
    with col_c2:
        city_b = st.selectbox("Ville B", city_list,
                               index=city_list.index("Douala") if "Douala" in city_list else 1)

    if st.button("⚡ Comparer en temps réel", width='stretch'):
        col_a, col_b = st.columns(2)
        for col, city_name in [(col_a, city_a), (col_b, city_b)]:
            with col:
                city_row = cities[cities["city"] == city_name].iloc[0]
                lat, lon = float(city_row["latitude"]), float(city_row["longitude"])
                region_enc, city_enc = get_region_city_enc(city_name, cities)
                with st.spinner(f"Prédiction {city_name}..."):
                    meteo = fetch_realtime_meteo(lat, lon, days=7)
                if meteo is not None and len(meteo):
                    # PM2.5 aujourd'hui
                    feat_today = build_feature_row(
                        meteo.iloc[0], lat, lon, region_enc, city_enc)
                    pm25_today = predict_pm25(model, feat_today, features)
                    lvl, css = pm25_level(pm25_today)
                    color = pm25_color(pm25_today)
                    ratio = round(pm25_today / stats["seuil_oms"], 1)

                    # Prévisions 7j
                    pm25_7 = []
                    for _, row in meteo.iterrows():
                        feat = build_feature_row(row, lat, lon, region_enc, city_enc)
                        pm25_7.append(predict_pm25(model, feat, features))

                    st.markdown(
                        f'<div class="card">'
                        f'<div class="hero-city">{city_name}</div>'
                        f'<div class="hero-region">{city_row["region"]}</div>'
                        f'<div style="margin:14px 0">'
                        f'<div class="hero-pm25-value" style="color:{color}">'
                        f'{pm25_today:.1f}<span class="hero-pm25-unit">µg/m³</span></div>'
                        f'<div class="hero-badge" style="color:{color};'
                        f'border-color:{color}40;background:{color}15">'
                        f'● {lvl} · ×{ratio} OMS</div></div>'
                        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px">',
                        unsafe_allow_html=True,
                    )
                    # Mini forecast
                    for d, v in zip(meteo["time"], pm25_7):
                        c_i = pm25_color(v)
                        st.markdown(
                            f'<span style="font-size:.72rem;font-family:\'IBM Plex Mono\';'
                            f'color:{c_i};background:{c_i}15;border:1px solid {c_i}30;'
                            f'border-radius:4px;padding:2px 6px">'
                            f'{d.strftime("%d")}: {v:.1f}</span>',
                            unsafe_allow_html=True,
                        )
                    st.markdown('</div></div>', unsafe_allow_html=True)

    # ── Table détaillée ───────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Table détaillée — PM2.5 prédit</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    if len(df_filtered):
        rows = []
        for _, r in df_filtered.iterrows():
            lvl, css = pm25_level(r["pm25_moy"])
            color = pm25_color(r["pm25_moy"])
            ratio = round(r["pm25_moy"] / stats["seuil_oms"], 1)
            pct_bar = min(r["pm25_moy"] / 45 * 100, 100)
            bar_html = (
                f'<div style="width:80px;height:4px;background:#21262d;'
                f'border-radius:2px;overflow:hidden">'
                f'<div style="width:{pct_bar:.0f}%;height:100%;'
                f'background:{color};border-radius:2px"></div></div>'
            )
            rows.append(
                f'<tr>'
                f'<td class="bold">{r["city"]}</td>'
                f'<td style="color:#8b949e;font-size:.8rem">{r["region"]}</td>'
                f'<td class="mono" style="color:{color}">{r["pm25_moy"]:.1f}</td>'
                f'<td>{bar_html}</td>'
                f'<td class="mono">×{ratio}</td>'
                f'<td><span class="badge badge-{css}">{lvl}</span></td>'
                f'</tr>'
            )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Ville</th><th>Région</th><th>PM2.5 (µg/m³)</th>'
            '<th>Barre</th><th>Ratio OMS</th><th>Niveau</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>',
            unsafe_allow_html=True,
        )


render()
