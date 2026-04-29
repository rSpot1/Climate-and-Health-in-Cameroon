"""
pages/apropos.py — À propos, guide, méthodologie, modèle, sources, support
"""
from __future__ import annotations
import streamlit as st
from utils.data import load_global_stats, load_features


def _endpoint(method, path, desc, params=None, response=""):
    method_css = "api-get" if method == "GET" else "api-post"
    params_html = ""
    if params:
        rows = "".join(
            f'<tr><td style="font-family:\'IBM Plex Mono\';color:#f0a500;font-size:.78rem">{p}</td>'
            f'<td style="font-size:.78rem;color:#8b949e;padding-left:.75rem">{d}</td></tr>'
            for p, d in params
        )
        params_html = f'<table style="margin:.5rem 0;border-collapse:collapse">{rows}</table>'
    resp_html = (
        f'<pre style="background:#0d1117;border:1px solid #30363d;border-radius:4px;'
        f'padding:.5rem .75rem;font-size:.75rem;color:#8b949e;margin:.5rem 0;'
        f'overflow-x:auto">{response}</pre>'
        if response else ""
    )
    return (
        f'<div class="card" style="margin-bottom:.75rem">'
        f'<div style="margin-bottom:.5rem">'
        f'<span class="api-method {method_css}">{method}</span>'
        f'<code style="font-family:\'IBM Plex Mono\';font-size:.82rem;color:#e6edf3">{path}</code>'
        f'</div><p style="font-size:.82rem;color:#8b949e;margin:.25rem 0">{desc}</p>'
        f'{params_html}{resp_html}</div>'
    )


def render():
    stats    = load_global_stats()
    features = load_features()

    st.markdown('<p class="page-title">À propos</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Guide d\'utilisation · Méthodologie · Modèle IA · '
        'Pollution & santé · Sources · Support technique</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        " Guide", " Méthodologie", " Modèle & Features",
        "🫁 Pollution & Santé", " Sources", " Support",
    ])

    # ── Tab 1 : Guide d'utilisation ───────────────────────────────────────────
    with tab1:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Guide d\'utilisation de l\'application</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        guides = [
            (" Accueil",
             "Page principale de surveillance. Sélectionnez une ville pour obtenir le PM2.5 "
             "prédit par le modèle AlphaInfera en temps réel (données Open-Meteo → RF → PM2.5). "
             "Les 4 KPIs météo (température, vent, précipitations, radiation) sont issus de l'API. "
             "Les prévisions 7 jours sont calculées journée par journée par le modèle. "
             "Les alertes nationales reflètent les niveaux prédits de la risk_table."),
            (" Prédicteur",
             "Entrez des paramètres météo manuellement ou chargez automatiquement les données "
             "Open-Meteo d'une ville via le bouton 📡. Le modèle calcule "
             "instantanément le PM2.5 prédit avec une jauge visuelle, un rapport au seuil OMS, "
             "et une recommandation santé personnalisée. Les prévisions 7j sont aussi affichées."),
            (" Tableau de bord",
             "Vue d'ensemble temporelle. Les jauges en haut affichent le PM2.5 prédit "
             "aujourd'hui pour les 5 villes clés (données Open-Meteo temps réel → modèle). "
             "La série temporelle régionale est calculée à partir des PM2.5 de la risk_table "
             "modulés par la saisonnalité calibrée sur le notebook. "
             "La heatmap montre la saisonnalité par région. Le scatter visualise la corrélation "
             "stagnation des vents / PM2.5 prédit."),
            (" Analyse spatiale",
             "Carte interactive de tous les PM2.5 prédits par ville (risk_table). "
             "Filtrez par niveau de risque ou région. Comparez deux villes en temps réel : "
             "le modèle est appelé avec les données Open-Meteo actuelles pour les deux villes "
             "et affiche les prévisions 7j côte à côte."),
            ("ℹ À propos",
             "Cette page : guide, méthodologie, documentation technique, "
             "effets de la pollution sur la santé, sources et contact support."),
        ]

        for title, content in guides:
            with st.expander(title):
                st.markdown(
                    f'<div style="font-size:.88rem;color:#8b949e;line-height:1.7">{content}</div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 2 : Méthodologie ──────────────────────────────────────────────────
    with tab2:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Contexte</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "Le Cameroun est confronté à une dégradation de la qualité de l'air aggravée par la "
            "variabilité climatique — pics de chaleur, stagnation des vents, harmattan. Ce projet "
            "développé dans le cadre du **Hackathon IndabaX Cameroon 2026** construit un système "
            "de prédiction et de surveillance du PM2.5 à partir des seules données météorologiques, "
            "en l'absence de capteurs dédiés sur l'ensemble du territoire."
        )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Pipeline</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        steps = [
            ("Collecte",             f"{stats['n_observations']:,} observations · {stats['n_villes']} villes · {stats['n_regions']} régions · 2020–2025"),
            ("EDA",                  "Distributions, saisonnalité, corrélations, profils régionaux"),
            ("Feature Engineering",  "24 features dérivées : stagnation, encodage cyclique, stress hydrique, géographie"),
            ("Proxy PM2.5",          "Variable cible construite à partir des corrélations météo→PM2.5 (Afrique sub-saharienne)"),
            ("Modélisation",         "7 modèles comparés : LR, Ridge, Arbre, RF×2, GBM, XGBoost + Grid Search"),
            ("Validation",           "Split chronologique 80/20 · KFold k=5 shuffle=False · MAE, RMSE, R²"),
            ("Séries temporelles",   "ARIMA, Prophet, LSTM évalués sur série univariée (Abong-Mbang)"),
            ("Déploiement",          "Export joblib · API Open-Meteo temps réel · Application Streamlit + Mobile Flutter"),
        ]
        rows = "".join(f'<tr><td class="bold">{s}</td><td>{d}</td></tr>' for s, d in steps)
        st.markdown(
            '<table class="data-table"><thead><tr><th>Étape</th><th>Détail</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Résultats clés</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "Meilleur modèle", "RF Optimisé"),
            (c2, "MAE Test",        f"{stats['best_model_mae']:.4f}"),
            (c3, "R² Test",         f"{stats['best_model_r2']:.4f}"),
            (c4, "Seuil OMS",       "15 µg/m³"),
        ]:
            with col:
                st.markdown(
                    f'<div class="metric-tile"><span class="metric-label">{label}</span>'
                    f'<span class="metric-value" style="font-size:1.1rem">{val}</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "**Importance des features (Gini) :**\n\n"
            "1. `is_no_rain` — Absence de précipitations **(0,461)** : premier déterminant\n"
            "2. `is_dry_season` — Saison sèche nov–mars **(0,235)**\n"
            "3. `temperature_2m_mean` — Température moyenne **(0,136)**\n"
            "4. `precipitation_sum` — Cumul précipitations **(0,126)**\n"
            "5. `shortwave_radiation_sum` — Radiation solaire **(0,036)**"
        )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">API REST — Documentation</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

    # ── Tab 3 : Modèle & Features ─────────────────────────────────────────────
    with tab3:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Modèle sélectionné</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "**RF Optimisé (GridSearch)** — `RandomForestRegressor`\n\n"
            "Retenu pour le déploiement : le modèle linéaire (MAE≈0) reproduit un artefact "
            "(proxy construit linéairement). Le RF Optimisé est le meilleur modèle non-linéaire, "
            "stable en validation croisée et généralisable à des données PM2.5 réelles.\n\n"
            "**Hyperparamètres :** `max_depth=16, min_samples_leaf=5, n_estimators=200`"
        )
        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "MAE Test",    "0.0503"),
            (c2, "RMSE Test",   "0.1108"),
            (c3, "R² Test",     "0.9994"),
            (c4, "MAE CV k=5",  "0.076±0.002"),
        ]:
            with col:
                st.markdown(
                    f'<div class="metric-tile"><span class="metric-label">{label}</span>'
                    f'<span class="metric-value" style="font-size:1rem;font-family:\'IBM Plex Mono\'">{val}</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Features du modèle (24)</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        feature_meta = {
            "temperature_2m_mean":         ("Météo brute",  "Température moyenne journalière (°C)"),
            "temperature_2m_max":          ("Météo brute",  "Température maximale (°C)"),
            "temperature_2m_min":          ("Météo brute",  "Température minimale (°C)"),
            "precipitation_sum":           ("Météo brute",  "Précipitations cumulées (mm)"),
            "wind_speed_10m_max":          ("Météo brute",  "Vitesse max du vent à 10m (km/h)"),
            "wind_gusts_10m_max":          ("Météo brute",  "Rafales max à 10m (km/h)"),
            "shortwave_radiation_sum":     ("Météo brute",  "Radiation solaire (MJ/m²)"),
            "et0_fao_evapotranspiration":  ("Météo brute",  "Évapotranspiration FAO (mm/j)"),
            "sunshine_ratio":              ("Dérivée",      "Durée ensoleillement / durée du jour"),
            "temp_amplitude":              ("Dérivée",      "Amplitude thermique max−min (°C)"),
            "is_no_wind":                  ("Dérivée",      "Indicateur vent < 5 km/h (stagnation)"),
            "is_no_rain":                  ("Dérivée",      "Indicateur précipitations < 0,1 mm"),
            "is_dry_season":               ("Dérivée",      "Saison sèche nov–mars (binaire)"),
            "month_sin":                   ("Temporel",     "Encodage cyclique du mois (sin)"),
            "month_cos":                   ("Temporel",     "Encodage cyclique du mois (cos)"),
            "day_of_year":                 ("Temporel",     "Jour de l'année (1–365)"),
            "temp_lag1":                   ("Lag",          "Température J-1"),
            "temp_lag7":                   ("Lag",          "Température J-7"),
            "wind_lag1":                   ("Lag",          "Vent max J-1"),
            "temp_roll7":                  ("Lag",          "Moyenne mobile température 7j"),
            "latitude":                    ("Géographique", "Latitude décimale"),
            "longitude":                   ("Géographique", "Longitude décimale"),
            "region_enc":                  ("Géographique", "Région encodée (LabelEncoder)"),
            "city_enc":                    ("Géographique", "Ville encodée (LabelEncoder)"),
        }
        cat_colors = {
            "Météo brute":  "#388bfd",
            "Dérivée":      "#f0a500",
            "Temporel":     "#3fb950",
            "Lag":          "#bc8cff",
            "Géographique": "#79c0ff",
        }
        rows_feat = []
        for feat in features:
            cat, desc = feature_meta.get(feat, ("—", "—"))
            c = cat_colors.get(cat, "#8b949e")
            rows_feat.append(
                f'<tr><td class="mono">{feat}</td>'
                f'<td><span style="font-size:.7rem;color:{c};font-family:\'IBM Plex Mono\'">{cat}</span></td>'
                f'<td style="font-size:.8rem;color:#8b949e">{desc}</td></tr>'
            )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Feature</th><th>Catégorie</th><th>Description</th>'
            '</tr></thead><tbody>' + "".join(rows_feat) + '</tbody></table>',
            unsafe_allow_html=True,
        )

    # ── Tab 4 : Pollution & Santé ─────────────────────────────────────────────
    with tab4:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Effets des particules fines PM2.5 sur la santé</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "Les particules fines (**PM2.5**, diamètre < 2,5 µm) pénètrent profondément dans "
            "les alvéoles pulmonaires et passent dans la circulation sanguine, provoquant :"
        )
        effets = [
            ("", "Maladies respiratoires", "Asthme, bronchite chronique, BPCO, infections respiratoires récurrentes"),
            ("", "Maladies cardiovasculaires", "Infarctus du myocarde, AVC, hypertension artérielle, arythmies"),
            ("", "Cancer du poumon", "Classé Groupe 1 carcinogène par le CIRC/OMS — exposition chronique"),
            ("", "Effets neurologiques", "Déclin cognitif, démence précoce, troubles du développement neuronal"),
            ("", "Impact sur les enfants", "Faible poids à la naissance, retards de développement, asthme précoce"),
            ("", "Infections aggravées", "COVID-19, tuberculose, pneumonies plus sévères en zone polluée"),
        ]
        col1, col2 = st.columns(2)
        for i, (icon, title, desc) in enumerate(effets):
            with (col1 if i % 2 == 0 else col2):
                st.markdown(
                    f'<div class="card" style="margin-bottom:10px">'
                    f'<div style="font-size:1.3rem;margin-bottom:6px">{icon}</div>'
                    f'<div style="font-weight:600;color:#e6edf3;font-size:.9rem">{title}</div>'
                    f'<div style="font-size:.8rem;color:#8b949e;margin-top:4px;line-height:1.5">{desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Chiffres clés — OMS / IHME 2023</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        kpis = [
            ("7 M", "décès prématurés/an", "liés à la pollution de l'air (OMS)"),
            ("99%", "de la population", "respire un air hors normes OMS"),
            ("780K", "décès/an", "en Afrique subsaharienne liés aux PM2.5"),
            ("22–30", "µg/m³ PM2.5", "moy. annuelle dans le nord Cameroun"),
            ("40%", "des décès PM2.5", "en Afrique : enfants < 5 ans"),
            ("×2–3", "PM2.5 Harmattan", "dans l'Extrême-Nord (nov.–mars)"),
        ]
        cols_kpi = st.columns(3)
        for i, (val, unit, desc) in enumerate(kpis):
            with cols_kpi[i % 3]:
                st.markdown(
                    f'<div class="metric-tile" style="margin-bottom:10px">'
                    f'<span class="metric-value" style="color:#f0a500">{val}</span>'
                    f'<span class="metric-label">{unit}</span>'
                    f'<span style="font-size:.72rem;color:#6e7681">{desc}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="alert-banner alert-info" style="margin-top:16px"> '
            '<div><div class="alert-title">Directive OMS 2021</div>'
            'Valeur guide PM2.5 : <b>15 µg/m³</b> en moyenne annuelle. '
            'L\'exposition chronique, même à des niveaux modérés, '
            'réduit l\'espérance de vie de 1 à 3 ans selon la région.</div></div>',
            unsafe_allow_html=True,
        )

    # ── Tab 5 : Sources ───────────────────────────────────────────────────────
    with tab5:
        sources = [
            ("Dataset principal",     "IndabaX Cameroon 2026",               f"{stats['n_observations']:,} obs · {stats['n_villes']} villes · 2020–2025",  "Organisateurs hackathon"),
            ("Météo temps réel",      "Open-Meteo API",                       "API ouverte · résolution 1 km · cache 30 min",                               "https://open-meteo.com"),
            ("Modèle RF",             "scikit-learn RandomForestRegressor",   f"v1.4 · MAE={stats['best_model_mae']:.4f} · R²={stats['best_model_r2']:.4f}","scikit-learn.org"),
            ("Cartographie",          "Carto Dark Matter",                    "Fond de carte sombre · OpenStreetMap",                                       "carto.com"),
            ("Seuil qualité de l'air","OMS — Lignes directrices 2021",       "PM2.5 annuel : 15 µg/m³",                                                   "who.int/air-quality"),
            ("Statistiques santé",    "IHME Global Burden of Disease 2023",  "Impact des PM2.5 en Afrique sub-saharienne",                                 "healthdata.org"),
            ("Recherche de base",     "Jeuland & Pattanayak (2012)",         "PM2.5 et météo en Afrique",                                                  "—"),
        ]
        rows_src = "".join(
            f'<tr><td class="bold">{s}</td><td>{src}</td>'
            f'<td style="color:#8b949e;font-size:.8rem">{d}</td>'
            f'<td class="mono" style="font-size:.75rem">{ref}</td></tr>'
            for s, src, d, ref in sources
        )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Composant</th><th>Source</th><th>Description</th><th>Référence</th>'
            '</tr></thead><tbody>' + rows_src + '</tbody></table>',
            unsafe_allow_html=True,
        )

    # ── Tab 6 : Support ───────────────────────────────────────────────────────
    with tab6:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Support technique</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="card card-accent" style="max-width:420px">'
            '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">'
            '<div style="width:44px;height:44px;border-radius:50%;'
            'background:linear-gradient(135deg,#f0a500,#388bfd);'
            'display:flex;align-items:center;justify-content:center;font-size:20px">👤</div>'
            '<div>'
            '<div style="font-size:1rem;font-weight:700;color:#e6edf3">Barka Fidèle</div>'
            '<div style="font-size:.78rem;color:#8b949e">Data Scientist</div>'
            '</div></div>'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
            '<span style="font-size:.9rem">📧</span>'
            '<a href="mailto:barkafidele@yahoo.com" style="color:#388bfd;font-family:\'IBM Plex Mono\';'
            'font-size:.85rem;text-decoration:none">barkafidele@yahoo.com</a>'
            '</div>'
            '<div style="font-size:.75rem;color:#6e7681;margin-top:10px;border-top:1px solid #21262d;padding-top:10px">'
            'IndabaX Cameroon 2026 · AlphaInfera Team · AirQual CM v1.0.0'
            '</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">À propos de l\'application</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="card"><p style="font-size:.82rem;color:#8b949e;margin:0;line-height:1.7">'
            f'<b style="color:#e6edf3">AirQual CM</b> · v1.0.0 <br>'
            f'Modèle <b style="color:#f0a500">RF AlphaInfera</b> (GridSearch) · '
            f'MAE = {stats["best_model_mae"]:.4f} · R² = {stats["best_model_r2"]:.4f}<br>'
            f'Données : Open-Meteo API · {stats["n_villes"]} villes · {stats["n_regions"]} régions '
            f'· {stats["n_observations"]:,} observations d\'entraînement<br>'
            f'Seuil OMS : 15 µg/m³ · Période couverte : {stats["periode_debut"]} → {stats["periode_fin"]}'
            f'</p></div>',
            unsafe_allow_html=True,
        )


render()
