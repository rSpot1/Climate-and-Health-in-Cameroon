"""
pages/apropos.py — Méthodologie, API publique, sources de données
"""
from __future__ import annotations

import streamlit as st

from utils.data import load_global_stats, load_features


def _endpoint(method: str, path: str, desc: str, params: list[tuple] = None,
               response: str = "") -> str:
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
        f'</div>'
        f'<p style="font-size:.82rem;color:#8b949e;margin:.25rem 0">{desc}</p>'
        f'{params_html}{resp_html}</div>'
    )


def render():
    stats    = load_global_stats()
    features = load_features()

    st.markdown('<p class="page-title">A propos</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-subtitle">Méthodologie, documentation API et sources de données.</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Méthodologie", "API publique", "Modèle & features", "Sources"])

    # ── Tab 1 : Méthodologie ──────────────────────────────────────────────────
    with tab1:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Contexte</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            Le Cameroun est confronté à une dégradation de la qualité de l'air aggravée par la
            variabilité climatique — pics de chaleur, stagnation des vents, harmattan. Ce projet
            développé dans le cadre du **Hackathon IndabaX Cameroon 2026** vise à construire un
            système de prédiction et de surveillance de la qualité de l'air (PM2.5) à partir
            des seules données météorologiques, en l'absence de capteurs dédiés sur l'ensemble du territoire.
            """,
        )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Pipeline</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        steps = [
            ("Collecte", f"{stats['n_observations']:,} observations · {stats['n_villes']} villes · {stats['n_regions']} régions · 2020–2025"),
            ("EDA", "Analyse des distributions, saisonnalité, corrélations, profils régionaux"),
            ("Feature Engineering", "24 features dérivées : indicateurs de stagnation, encodage cyclique, stress hydrique, géographie"),
            ("Proxy PM2.5", "Variable cible construite à partir des corrélations météo→PM2.5 en Afrique sub-saharienne"),
            ("Modélisation", "7 modèles comparés : LR, Ridge, Arbre, RF×2, GBM, XGBoost + Grid Search"),
            ("Validation", "Split chronologique 80/20 · KFold k=5 shuffle=False · MAE, RMSE, R²"),
            ("Séries temporelles", "ARIMA, Prophet, LSTM évalués sur série univariée (Abong-Mbang)"),
            ("Déploiement", "Export joblib · API Open-Meteo temps réel · Application Streamlit"),
        ]

        rows = "".join(
            f'<tr><td class="bold">{s}</td><td>{d}</td></tr>'
            for s, d in steps
        )
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
            (c2, "MAE Test", f"{stats['best_model_mae']:.4f}"),
            (c3, "R² Test", f"{stats['best_model_r2']:.4f}"),
            (c4, "Seuil OMS", "15 µg/m³"),
        ]:
            with col:
                st.markdown(
                    f'<div class="metric-tile"><span class="metric-label">{label}</span>'
                    f'<span class="metric-value" style="font-size:1.1rem">{val}</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            **Facteurs aggravants identifiés (par ordre d'importance Gini) :**

            1. `is_no_rain` — Absence de précipitations (0,461) : premier déterminant, pas de lessivage atmosphérique
            2. `is_dry_season` — Saison sèche nov–mars (0,235)
            3. `temperature_2m_mean` — Température moyenne (0,136)
            4. `precipitation_sum` — Cumul de précipitations (0,126)
            5. `shortwave_radiation_sum` — Radiation solaire (0,036)
            """,
        )

    # ── Tab 2 : API publique ──────────────────────────────────────────────────
    with tab2:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">API REST — AirQual Cameroun</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="alert-banner alert-info"><div>'
            '<div class="alert-title">API en développement</div>'
            'Les endpoints ci-dessous documentent l\'API cible déployable via FastAPI. '
            'Base URL : <code style="font-family:\'IBM Plex Mono\'">https://api.airqual-cm.org/v1</code>'
            '</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="section-label" style="margin-top:1rem">Données</p>', unsafe_allow_html=True)

        st.markdown(_endpoint(
            "GET", "/cities",
            "Liste toutes les villes surveillées avec leurs coordonnées et profils climatiques.",
            response='[\n  {"city":"Maroua","region":"Extreme-Nord","lat":10.60,"lon":14.33,...},\n  ...\n]'
        ), unsafe_allow_html=True)

        st.markdown(_endpoint(
            "GET", "/risk",
            "Table de risque PM2.5 agrégée par ville (moyenne, P95, stagnation, niveau).",
            params=[
                ("region", "Filtrer par région (optionnel)"),
                ("niveau", "Filtrer par niveau : Faible | Modere | Eleve | Tres eleve"),
            ],
            response='[\n  {"city":"Maroua","pm25_moy":26.8,"pm25_p95":38.2,"niveau_risque":"Tres eleve"},\n  ...\n]'
        ), unsafe_allow_html=True)

        st.markdown(_endpoint(
            "GET", "/meteo/{city}",
            "Données météo temps réel d'une ville (proxy Open-Meteo, TTL 30 min).",
            params=[
                ("city", "Nom de la ville (ex : Maroua, Yaounde)"),
                ("days", "Horizon de prévision en jours (1–7, défaut : 3)"),
            ],
            response='{\n  "city": "Maroua",\n  "date": "2025-03-04",\n  "temperature_2m_mean": 34.2,\n  "precipitation_sum": 0.0,\n  ...\n}'
        ), unsafe_allow_html=True)

        st.markdown('<p class="section-label" style="margin-top:1.5rem">Prédiction</p>', unsafe_allow_html=True)

        st.markdown(_endpoint(
            "POST", "/predict",
            "Prédit le PM2.5 à partir de paramètres météorologiques arbitraires.",
            params=[
                ("temperature_2m_mean", "float — Température moyenne (°C)"),
                ("precipitation_sum",   "float — Précipitations (mm)"),
                ("wind_speed_10m_max",  "float — Vent max (km/h)"),
                ("shortwave_radiation_sum", "float — Radiation solaire (MJ/m²)"),
                ("latitude / longitude", "float — Coordonnées"),
                ("month",              "int — Mois (1–12)"),
            ],
            response='{\n  "pm25_predicted": 23.41,\n  "niveau": "Eleve",\n  "ratio_oms": 1.56,\n  "model": "RF Optimise (GridSearch)"\n}'
        ), unsafe_allow_html=True)

        st.markdown(_endpoint(
            "GET", "/predict/{city}",
            "Prédit le PM2.5 pour une ville donnée à partir des données météo temps réel.",
            params=[
                ("city", "Nom de la ville"),
                ("date", "Date cible YYYY-MM-DD (optionnel, défaut : aujourd'hui + 1)"),
            ],
            response='{\n  "city": "Maroua",\n  "date": "2025-03-05",\n  "pm25_predicted": 27.2,\n  "niveau": "Tres eleve"\n}'
        ), unsafe_allow_html=True)

        st.markdown('<p class="section-label" style="margin-top:1.5rem">Alertes</p>', unsafe_allow_html=True)

        st.markdown(_endpoint(
            "GET", "/alerts",
            "Retourne les alertes PM2.5 actives pour toutes les villes.",
            params=[
                ("min_niveau", "Niveau minimum à inclure : Modere | Eleve | Tres eleve"),
            ],
            response='[\n  {"city":"Maroua","niveau":"Tres eleve","pm25":27.2,"message":"Exposition chronique — groupes vulnérables"},\n  ...\n]'
        ), unsafe_allow_html=True)

        # Exemple cURL
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Exemple d\'appel</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )
        st.code(
            'curl -X POST "https://api.airqual-cm.org/v1/predict" \\\n'
            '  -H "Content-Type: application/json" \\\n'
            '  -d \'{\n'
            '    "temperature_2m_mean": 32.5,\n'
            '    "precipitation_sum": 0.0,\n'
            '    "wind_speed_10m_max": 4.2,\n'
            '    "shortwave_radiation_sum": 21.0,\n'
            '    "latitude": 10.60, "longitude": 14.33,\n'
            '    "month": 2\n'
            '  }\'',
            language="bash",
        )

    # ── Tab 3 : Modèle & features ─────────────────────────────────────────────
    with tab3:
        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Modèle sélectionné</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            **RF Optimisé (GridSearch)** — `RandomForestRegressor`

            Le RF Optimisé est retenu pour le déploiement au lieu du modèle linéaire (MAE = 0)
            car ce dernier reproduit un artefact : le proxy PM2.5 est construit comme une
            combinaison linéaire des features, ce qui rend sa reconstruction analytiquement triviale.
            Sur des données PM2.5 observées réelles, la linéarité n'est pas garantie.
            Le RF Optimisé (MAE = 0,050, R² = 0,999) est le meilleur modèle non-linéaire,
            stable en validation croisée (MAE CV = 0,076 ± 0,002) et généralisable.

            **Hyperparamètres optimaux :** `max_depth=16, min_samples_leaf=5, n_estimators=200`
            """,
        )

        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "MAE Test",      "0.0503"),
            (c2, "RMSE Test",     "0.1108"),
            (c3, "R² Test",       "0.9994"),
            (c4, "MAE CV (k=5)",  "0.076 ± 0.002"),
        ]:
            with col:
                st.markdown(
                    f'<div class="metric-tile"><span class="metric-label">{label}</span>'
                    f'<span class="metric-value" style="font-size:1.1rem;font-family:\'IBM Plex Mono\'">{val}</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="section-divider"><div class="section-divider-line"></div>'
            '<span class="section-divider-text">Features du modèle</span>'
            '<div class="section-divider-line"></div></div>',
            unsafe_allow_html=True,
        )

        feature_meta = {
            "temperature_2m_mean":          ("Météo brute", "Température moyenne journalière (°C)"),
            "temperature_2m_max":           ("Météo brute", "Température maximale (°C)"),
            "temperature_2m_min":           ("Météo brute", "Température minimale (°C)"),
            "precipitation_sum":            ("Météo brute", "Précipitations cumulées (mm)"),
            "wind_speed_10m_max":           ("Météo brute", "Vitesse max du vent à 10m (km/h)"),
            "wind_gusts_10m_max":           ("Météo brute", "Rafales max à 10m (km/h)"),
            "shortwave_radiation_sum":      ("Météo brute", "Radiation solaire (MJ/m²)"),
            "et0_fao_evapotranspiration":   ("Météo brute", "Évapotranspiration FAO (mm/j)"),
            "sunshine_ratio":               ("Dérivée",     "Durée ensoleillement / durée du jour"),
            "temp_amplitude":               ("Dérivée",     "Amplitude thermique max−min (°C)"),
            "is_no_wind":                   ("Dérivée",     "Indicateur vent < 5 km/h (stagnation)"),
            "is_no_rain":                   ("Dérivée",     "Indicateur précipitations < 0,1 mm"),
            "is_dry_season":                ("Dérivée",     "Saison sèche nov–mars (binaire)"),
            "month_sin":                    ("Temporel",    "Encodage cyclique du mois (sin)"),
            "month_cos":                    ("Temporel",    "Encodage cyclique du mois (cos)"),
            "day_of_year":                  ("Temporel",    "Jour de l'année (1–365)"),
            "temp_lag1":                    ("Lag",         "Température J-1"),
            "temp_lag7":                    ("Lag",         "Température J-7"),
            "wind_lag1":                    ("Lag",         "Vent max J-1"),
            "temp_roll7":                   ("Lag",         "Moyenne mobile température 7j"),
            "latitude":                     ("Géographique","Latitude décimale"),
            "longitude":                    ("Géographique","Longitude décimale"),
            "region_enc":                   ("Géographique","Région encodée (LabelEncoder)"),
            "city_enc":                     ("Géographique","Ville encodée (LabelEncoder)"),
        }

        rows_feat = []
        for feat in features:
            cat, desc = feature_meta.get(feat, ("—", "—"))
            cat_colors = {
                "Météo brute": "#388bfd", "Dérivée": "#f0a500",
                "Temporel": "#3fb950", "Lag": "#bc8cff", "Géographique": "#79c0ff",
            }
            c = cat_colors.get(cat, "#8b949e")
            rows_feat.append(
                f'<tr>'
                f'<td class="mono">{feat}</td>'
                f'<td><span style="font-size:.7rem;color:{c};font-family:\'IBM Plex Mono\'">{cat}</span></td>'
                f'<td style="font-size:.8rem;color:#8b949e">{desc}</td>'
                f'</tr>'
            )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Feature</th><th>Catégorie</th><th>Description</th>'
            '</tr></thead><tbody>' + "".join(rows_feat) + '</tbody></table>',
            unsafe_allow_html=True,
        )

    # ── Tab 4 : Sources ───────────────────────────────────────────────────────
    with tab4:
        sources = [
            ("Dataset principal", "IndabaX Cameroon 2026", "87 240 observations météo · 40 villes · 2020–2025", "Fourni par les organisateurs"),
            ("Météo temps réel", "Open-Meteo API", "API ouverte · résolution 1 km · TTL cache 30 min", "https://open-meteo.com"),
            ("Cartographie", "Carto Dark Matter", "Fond de carte sombre pour visualisation nocturne", "Carto / OpenStreetMap"),
            ("Modèle de référence", "scikit-learn RandomForestRegressor", "v1.4 · MAE=0.050 · R²=0.999", "scikit-learn.org"),
            ("Seuil qualité de l'air", "OMS — Lignes directrices 2021", "PM2.5 annuel : 15 µg/m³", "who.int/air-quality"),
            ("Recherche de base", "Jeuland & Pattanayak (2012), Balmes (2019)", "PM2.5 et météo en Afrique sub-saharienne", "—"),
        ]
        rows_src = "".join(
            f'<tr><td class="bold">{s}</td><td>{src}</td><td style="color:#8b949e;font-size:.8rem">{d}</td><td class="mono" style="font-size:.75rem">{ref}</td></tr>'
            for s, src, d, ref in sources
        )
        st.markdown(
            '<table class="data-table"><thead><tr>'
            '<th>Composant</th><th>Source</th><th>Description</th><th>Référence</th>'
            '</tr></thead><tbody>' + rows_src + '</tbody></table>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="card"><p style="font-size:.82rem;color:#8b949e;margin:0">'
            'Hackathon IndabaX Cameroon 2026 · Modèle RF Optimisé (GridSearch) · '
            f'MAE = {stats["best_model_mae"]:.4f} · R² = {stats["best_model_r2"]:.4f} · '
            'Données Open-Meteo · Seuil OMS 15 µg/m³</p></div>',
            unsafe_allow_html=True,
        )

# ── Point d'entrée Streamlit multi-pages ──
render()
