"""
pages/accueil.py — Tableau de bord principal avec PM2.5 prédits par le modèle
"""
from __future__ import annotations
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st

from utils.data import (
    fetch_realtime_meteo, load_city_profiles, load_global_stats,
    load_risk_table, load_model, load_features,
    build_feature_row, predict_pm25, pm25_level, pm25_color, oms_ratio,
)
from utils.charts import risk_map, city_bar, forecast_line

tz = pytz.timezone("Africa/Douala")


def _metric(label, value, unit="", delta="", delta_up=True, predicted=False):
    delta_class = "metric-delta-up" if delta_up else "metric-delta-down"
    delta_html  = f'<span class="{delta_class}">{delta}</span>' if delta else ""
    pred_html   = '<span class="metric-predicted">● Valeur prédite</span>' if predicted else ""
    return (
        f'<div class="metric-tile">'
        f'<span class="metric-label">{label}</span>'
        f'<span class="metric-value">{value}'
        f'<span class="metric-unit"> {unit}</span></span>'
        f'{delta_html}{pred_html}</div>'
    )


def _alert(title, body, level):
    icon = {"critical":"🔴","high":"🟠","medium":"🟡","info":"🔵"}.get(level,"⚪")
    return (
        f'<div class="alert-banner alert-{level}">'
        f'<span style="font-size:1.1rem">{icon}</span>'
        f'<div><div class="alert-title">{title}</div>'
        f'<span style="font-size:.82rem;color:#8b949e">{body}</span></div></div>'
    )


def render():
    stats   = load_global_stats()
    risk_df = load_risk_table()
    cities  = load_city_profiles()
    model   = load_model()
    features = load_features()
    now     = datetime.now(tz)
    model_active = model is not None

    # ── Header ────────────────────────────────────────────────────────────────
    col_h, col_live = st.columns([5, 1])
    with col_h:
        st.markdown('<p class="page-title">Surveillance de la qualité de l\'air</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="page-subtitle">Cameroun · {stats["n_villes"]} villes · '
            f'{stats["n_regions"]} régions</p>',
            unsafe_allow_html=True,
        )
    with col_live:
        mode_html = (
            '<span class="predicted-dot"></span>'
            '<span style="font-size:.72rem;color:#f0a500">Modèle actif</span>'
            if model_active else
            '<span class="predicted-dot"></span>'
            '<span style="font-size:.72rem;color:#f0a500">Proxy calibré</span>'
        )
        st.markdown(
            f'<div style="text-align:right;padding-top:1rem">'
            f'{mode_html}<br>'
            f'<span style="font-size:.68rem;color:#6e7681;font-family:\'IBM Plex Mono\'">'
            f'{now.strftime("%H:%M · %d %b %Y")}</span></div>',
            unsafe_allow_html=True,
        )

    # ── Ville principale — PM2.5 prédit en temps réel ────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Analyse en temps réel</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        city_list = cities["city"].tolist() if len(cities) else ["Maroua"]
        default_idx = city_list.index("Maroua") if "Maroua" in city_list else 0
        city_choice = st.selectbox("Ville", city_list, index=default_idx, label_visibility="collapsed")
    with col_btn:
        refresh = st.button(" Actualiser", width='stretch')

    if city_choice and len(cities):
        city_row = cities[cities["city"] == city_choice].iloc[0]
        lat, lon = float(city_row["latitude"]), float(city_row["longitude"])

        # Chercher encodages région/ville
        risk_row = risk_df[risk_df["city"] == city_choice] if "city" in risk_df.columns else pd.DataFrame()
        region_enc = sorted(cities["region"].unique().tolist()).index(city_row["region"]) \
            if city_row["region"] in sorted(cities["region"].unique().tolist()) else 0
        city_enc = city_list.index(city_choice) if city_choice in city_list else 0

        with st.spinner("Interrogation + prédiction..."):
            meteo = fetch_realtime_meteo(lat, lon, days=7)

        if meteo is not None and len(meteo):
            today = meteo.iloc[0]
            feat_row = build_feature_row(today, lat, lon, region_enc, city_enc)
            pm25_pred = predict_pm25(model, feat_row, features)
            lvl_label, lvl_css = pm25_level(pm25_pred)
            color = pm25_color(pm25_pred)
            ratio = oms_ratio(pm25_pred)

            # ── Hero PM2.5 ────────────────────────────────────────────────────
            st.markdown(
                f'<div class="hero-banner">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">'
                f'<div>'
                f'<div class="hero-city"> {city_choice}</div>'
                f'<div class="hero-region">{city_row["region"]} · {now.strftime("%d %b %Y")}</div>'
                f'<div style="margin-top:20px">'
                f'<div class="hero-pm25-value" style="color:{color}">{pm25_pred:.1f}'
                f'<span class="hero-pm25-unit">µg/m³</span></div>'
                f'<div class="hero-badge" style="color:{color};border-color:{color}40;background:{color}15">'
                f'● {lvl_label} · ×{ratio} seuil OMS</div>'
                f'</div></div>'
                f'<div style="text-align:right">'
                f'<div style="font-size:.7rem;color:#6e7681;text-transform:uppercase;letter-spacing:.08em">PM2.5 prédit</div>'
                f'<div style="font-size:.75rem;color:#f0a500;font-family:\'IBM Plex Mono\';margin-top:4px">'
                f' AlphaInfera</div>'
                f'<div style="font-size:.68rem;color:#6e7681;margin-top:2px">Précision : 0.99</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )

            # ── KPIs météo ────────────────────────────────────────────────────
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.markdown(_metric("Température moy.",
                    f"{today.get('temperature_2m_mean','—'):.0f}", "°C"), unsafe_allow_html=True)
            with mc2:
                st.markdown(_metric("Vent max.",
                    f"{today.get('wind_speed_10m_max',0) or 0:.0f}", "km/h"), unsafe_allow_html=True)
            with mc3:
                st.markdown(_metric("Précipitations",
                    f"{today.get('precipitation_sum',0) or 0:.1f}", "mm"), unsafe_allow_html=True)
            with mc4:
                st.markdown(_metric("Radiation",
                    f"{today.get('shortwave_radiation_sum',0) or 0:.0f}", "MJ/m²"), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Prévisions 7 jours PM2.5 prédits ─────────────────────────────
            st.markdown(
                '<div class="section-divider"><div class="section-divider-line"></div>'
                '<span class="section-divider-text">Prévisions 7 jours — PM2.5 prédit</span>'
                '<div class="section-divider-line"></div></div>',
                unsafe_allow_html=True,
            )

            dates_7, pm25_7 = [], []
            cols_fc = st.columns(min(7, len(meteo)))
            for i, (_, row) in enumerate(meteo.iterrows()):
                feat = build_feature_row(row, lat, lon, region_enc, city_enc)
                pm25_i = predict_pm25(model, feat, features)
                color_i = pm25_color(pm25_i)
                lvl_i, _ = pm25_level(pm25_i)
                date_str = row["time"].strftime("%a %d") if hasattr(row["time"], "strftime") else f"J+{i}"
                dates_7.append(row["time"])
                pm25_7.append(pm25_i)
                with cols_fc[i]:
                    st.markdown(
                        f'<div class="forecast-day-card">'
                        f'<div class="forecast-day-label">{date_str}</div>'
                        f'<div class="forecast-day-value" style="color:{color_i}">{pm25_i:.1f}</div>'
                        f'<div class="forecast-day-sub">µg/m³</div>'
                        f'<div style="font-size:.65rem;color:{color_i};margin-top:3px">{lvl_i}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            st.plotly_chart(forecast_line(dates_7, pm25_7, city_choice),
                            width='stretch', config={"displayModeBar": False})
        else:
            st.markdown(
                _alert("API indisponible",
                       "Impossible de contacter Open-Meteo. Données du cache affichées.", "medium"),
                unsafe_allow_html=True,
            )

    # ── Alertes nationales ────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Alertes nationales</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    now_month = now.month
    harmattan_active = now_month in [11, 12, 1, 2]
    critical_cities = risk_df[risk_df["pm25_moy"] > 25]["city"].tolist() if len(risk_df) else []
    high_cities     = risk_df[(risk_df["pm25_moy"] > 20) & (risk_df["pm25_moy"] <= 25)]["city"].tolist() if len(risk_df) else []

    if harmattan_active:
        st.markdown(_alert(
            " Saison Harmattan active",
            "Vents du Nord chargés en poussières sahéliennes. PM2.5 élevés attendus dans l'Extrême-Nord et le Nord.",
            "critical",
        ), unsafe_allow_html=True)

    if critical_cities:
        st.markdown(_alert(
            f" Niveau critique — {len(critical_cities)} ville(s)",
            f"PM2.5 prédit > 25 µg/m³ : {', '.join(critical_cities[:5])}. Groupes vulnérables : rester en intérieur.",
            "high",
        ), unsafe_allow_html=True)

    if high_cities:
        st.markdown(_alert(
            f" Niveau élevé — {len(high_cities)} ville(s)",
            f"PM2.5 prédit 20–25 µg/m³ : {', '.join(high_cities[:4])}. Vigilance recommandée.",
            "medium",
        ), unsafe_allow_html=True)

    if not harmattan_active and not critical_cities and not high_cities:
        st.markdown(_alert(
            " Qualité de l'air satisfaisante",
            "Aucune ville ne dépasse le seuil critique (25 µg/m³) selon le modèle.",
            "info",
        ), unsafe_allow_html=True)

    # ── KPIs nationaux ────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Indicateurs nationaux (valeurs prédites)</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    pm25_moy = stats["pm25_national_moy"]
    pm25_p95 = stats["pm25_national_p95"]
    ratio_national = round(pm25_moy / stats["seuil_oms"], 1)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(_metric("PM2.5 national moyen", f"{pm25_moy:.1f}", "µg/m³",
                             f"×{ratio_national} seuil OMS", delta_up=True, predicted=True),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(_metric("PM2.5 P95 national", f"{pm25_p95:.1f}", "µg/m³",
                             predicted=True), unsafe_allow_html=True)
    with c3:
        n_crit = len(risk_df[risk_df["pm25_moy"] > 25]) if len(risk_df) else 0
        st.markdown(_metric("Villes critiques (>25)", str(n_crit),
                             f"/ {stats['n_villes']}"), unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)

    # ── Carte nationale ───────────────────────────────────────────────────────
    col_map, col_rank = st.columns([3, 1])
    with col_map:
        st.markdown('<p class="section-label">Carte des PM2.5 prédits — toutes villes</p>', unsafe_allow_html=True)
        if len(risk_df):
            st.plotly_chart(risk_map(risk_df), width='stretch', config={"displayModeBar": False})

    with col_rank:
        st.markdown('<p class="section-label">Classement PM2.5 prédit</p>', unsafe_allow_html=True)
        if len(risk_df):
            top = risk_df.sort_values("pm25_moy", ascending=False).head(10).reset_index(drop=True)
            rows = []
            for _, r in top.iterrows():
                lvl, css = pm25_level(r["pm25_moy"])
                rows.append(
                    f'<tr><td class="bold">{r["city"]}</td>'
                    f'<td class="mono">{r["pm25_moy"]:.1f}</td>'
                    f'<td><span class="badge badge-{css}">{lvl[:6]}</span></td></tr>'
                )
            st.markdown(
                '<table class="data-table"><thead><tr>'
                '<th>Ville</th><th>µg/m³</th><th>Niveau</th>'
                '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>',
                unsafe_allow_html=True,
            )

    # ── Bar chart ─────────────────────────────────────────────────────────────
    if len(risk_df):
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">PM2.5 prédit par ville (top 20)</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(city_bar(risk_df.sort_values("pm25_moy", ascending=False).head(20)),
                        width='stretch', config={"displayModeBar": False})


render()
