# AirQual Cameroun — Application Streamlit

Surveillance prédictive de la qualité de l'air au Cameroun.
Hackathon IndabaX Cameroon 2026.

## Structure

```
airqual_app/
├── app.py                  # Point d'entrée principal
├── requirements.txt
├── assets/
│   └── style.css           # Design system (thème sombre)
├── models/                 # Artefacts exportés depuis le notebook
│   ├── best_model_rf.joblib
│   ├── features.json
│   ├── label_encoder_region.joblib
│   ├── city_profiles.csv
│   ├── risk_table.csv
│   └── global_stats.json
├── pages/
│   ├── accueil.py          # Carte de risque + alertes temps réel
│   ├── predicteur.py       # Formulaire météo → prédiction PM2.5
│   ├── dashboard.py        # Évolution temporelle par région
│   ├── spatial.py          # Analyse spatiale comparative
│   └── apropos.py          # Méthodologie + API publique
└── utils/
    ├── data.py             # Chargement modèle, API Open-Meteo, helpers
    └── charts.py           # Visualisations Plotly avec thème cohérent
```

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
# Copier d'abord les artefacts du notebook dans models/
# (exécuter la cellule d'export dans le notebook)

streamlit run app.py
```

## Pages

| Page | Description |
|------|-------------|
| Accueil | Carte de risque interactive, alertes temps réel, KPIs nationaux |
| Prédicteur | Formulaire météo ou API → prédiction PM2.5 + prévision 7 jours |
| Tableau de bord | Évolution temporelle, heatmap saisonnalité, stats par région |
| Analyse spatiale | Comparaison des villes, profils détaillés, scatter stagnation |
| A propos | Méthodologie, documentation API REST, features du modèle, sources |

## API publique (cible FastAPI)

L'onglet "A propos" documente les endpoints de l'API REST déployable :
- `GET /cities` — liste des villes
- `GET /risk` — table de risque PM2.5
- `GET /meteo/{city}` — météo temps réel
- `POST /predict` — prédiction PM2.5 sur paramètres arbitraires
- `GET /predict/{city}` — prédiction automatique via API météo
- `GET /alerts` — alertes actives

## Modèle

RF Optimisé (GridSearch) — `max_depth=16, min_samples_leaf=5, n_estimators=200`
MAE Test = 0.0503 · R² = 0.9994 · MAE CV = 0.076 ± 0.002

## Données météo temps réel

Open-Meteo API (https://open-meteo.com) — libre, sans clé API, TTL cache 30 min.
