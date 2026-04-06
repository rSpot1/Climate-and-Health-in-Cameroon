"""
pages/spatial.py — Analyse spatiale : comparaison des zones à risque
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data import load_city_profiles, load_risk_table, pm25_level
from utils.charts import risk_map, city_bar, stagnation_scatter


def render():
    risk_df = load_risk_table()
    cities  = load_city_profiles()

    st.markdown('<p class="page-title">Analyse spatiale</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Comparaison des zones à risque, profils climatiques '
        'et facteurs aggravants par localité.</p>',
        unsafe_allow_html=True,
    )

    # ── Filtres ───────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        nivs = ["Tous"] + sorted(risk_df["niveau_risque"].unique().tolist()) if "niveau_risque" in risk_df.columns else ["Tous"]
        niv_filter = st.selectbox("Filtrer par niveau de risque", nivs)
    with col_f2:
        sort_col = st.selectbox("Trier par", ["PM2.5 moyen", "PM2.5 P95", "Jours de stagnation"])

    sort_map = {
        "PM2.5 moyen": "pm25_moy",
        "PM2.5 P95":   "pm25_p95",
        "Jours de stagnation": "jours_stagnation",
    }
    s_col = sort_map[sort_col]

    df_filtered = risk_df.copy()
    if niv_filter != "Tous" and "niveau_risque" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["niveau_risque"] == niv_filter]
    if s_col in df_filtered.columns:
        df_filtered = df_filtered.sort_values(s_col, ascending=False)

    st.markdown("---")

    # ── Carte ──────────────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">Carte de risque</p>', unsafe_allow_html=True)
    if len(df_filtered):
        st.plotly_chart(risk_map(df_filtered, height=480),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Comparaison côte à côte ────────────────────────────────────────────────
    col_bar, col_sc = st.columns(2)

    with col_bar:
        st.markdown('<p class="section-label">PM2.5 moyen par ville (top 20)</p>', unsafe_allow_html=True)
        st.plotly_chart(city_bar(df_filtered.head(20)),
                        use_container_width=True, config={"displayModeBar": False})

    with col_sc:
        st.markdown('<p class="section-label">Stagnation vs PM2.5</p>', unsafe_allow_html=True)
        if len(df_filtered):
            st.plotly_chart(stagnation_scatter(df_filtered),
                            use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table détaillée ─────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Table détaillée</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    cols_show = [c for c in ["city","region","pm25_moy","pm25_p95","jours_stagnation","niveau_risque"]
                 if c in df_filtered.columns]
    if len(df_filtered):
        rows = []
        for _, r in df_filtered[cols_show].iterrows():
            lbl, css = pm25_level(float(r.get("pm25_moy", 18)))
            stag = r.get("jours_stagnation", "—")
            rows.append(
                f'<tr>'
                f'<td class="bold">{r.get("city","—")}</td>'
                f'<td>{r.get("region","—")}</td>'
                f'<td class="mono">{float(r.get("pm25_moy",0)):.2f}</td>'
                f'<td class="mono">{float(r.get("pm25_p95",0)):.2f}</td>'
                f'<td class="mono">{stag:.0f}' if isinstance(stag, float) else f'<td class="mono">{stag}'
                f'</td><td><span class="badge badge-{css}">{lbl}</span></td>'
                f'</tr>'
            )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Ville</th><th>Région</th><th>PM2.5 moy</th>'
            '<th>PM2.5 P95</th><th>Stagnation (j)</th><th>Niveau</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>',
            unsafe_allow_html=True,
        )

    # ── Profil détaillé d'une ville ───────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"><div class="section-divider-line"></div>'
        '<span class="section-divider-text">Profil détaillé par ville</span>'
        '<div class="section-divider-line"></div></div>',
        unsafe_allow_html=True,
    )

    city_sel = st.selectbox("Sélectionner une ville", df_filtered["city"].tolist() if len(df_filtered) else ["—"])

    if city_sel and city_sel != "—":
        r_row = risk_df[risk_df["city"] == city_sel]
        c_row = cities[cities["city"] == city_sel]

        if len(r_row) and len(c_row):
            r = r_row.iloc[0]
            c = c_row.iloc[0]
            lbl, css = pm25_level(float(r.get("pm25_moy", 18)))

            p1, p2, p3, p4 = st.columns(4)
            def tile(col, label, val, unit=""):
                with col:
                    st.markdown(
                        f'<div class="metric-tile"><span class="metric-label">{label}</span>'
                        f'<span class="metric-value">{val}<span class="metric-unit"> {unit}</span></span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            tile(p1, "PM2.5 moyen", f'{float(r.get("pm25_moy",0)):.2f}', "µg/m³")
            tile(p2, "Température", f'{float(c.get("temp_moy",0)):.1f}', "°C")
            tile(p3, "Précipitations méd.", f'{float(c.get("precip_moy",0)):.1f}', "mm")
            tile(p4, "Vent moyen", f'{float(c.get("vent_moy",0)):.1f}', "km/h")

            st.markdown("<br>", unsafe_allow_html=True)

            # Indicateurs aggravants
            p5, p6, p7, p8 = st.columns(4)
            tile(p5, "Radiation solaire", f'{float(c.get("radiation_moy",0)):.1f}', "MJ/m²")
            tile(p6, "ET0 médiane", f'{float(c.get("et0_moy",0)):.2f}', "mm/j")
            tile(p7, "Jours stagnation", f'{int(r.get("jours_stagnation",0))}', "j/an")
            p8.markdown(
                f'<div class="metric-tile"><span class="metric-label">Niveau risque</span>'
                f'<span class="badge badge-{css}" style="font-size:1rem;padding:.4rem .8rem;">{lbl}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Point d'entrée Streamlit multi-pages ──
render()
