# AirQual Cameroun — Surveillance prédictive de la qualité de l'air

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![IndabaX](https://img.shields.io/badge/IndabaX-Cameroon%202026-blue?style=for-the-badge)](https://indabax.cm)

##  Présentation

**AirQual Cameroun** est une application de surveillance et de prédiction de la qualité de l'air (particules fines PM2.5) développée dans le cadre du **Hackathon IndabaX Cameroon 2026**.

Le projet répond à un défi majeur : l'absence de capteurs de qualité de l'air sur l'ensemble du territoire camerounais. En utilisant uniquement des données météorologiques (température, vent, précipitations, etc.) et des techniques de Machine Learning, AirQual estime la concentration de PM2.5 pour 40 villes majeures du Cameroun.

##  Fonctionnalités

L'application est structurée en 5 modules complémentaires :

1.  ** Accueil** : Dashboard national avec alertes en temps réel, KPIs et carte de risque interactive.
2.  ** Prédicteur** : Formulaire interactif permettant de prédire le niveau de PM2.5. Supporte la saisie manuelle ou le chargement automatique des données météo via l'API Open-Meteo.
3.  ** Tableau de bord** : Analyse de l'évolution temporelle par région, heatmap de saisonnalité et statistiques détaillées.
4.  ** Analyse spatiale** : Comparaison des zones à risque et étude de la corrélation entre stagnation atmosphérique et pollution.
5.  ** À propos** : Détails sur la méthodologie, documentation de l'API REST et sources de données.

##  Installation et Lancement

### Prérequis
- Python 3.9 ou supérieur
- Un environnement virtuel (recommandé)

### Installation
```bash
git clone <url-du-repo>
cd Climate-and-Health-in-Cameroon
pip install -r requirements.txt
```

### Lancement
```bash
streamlit run app.py
```

##  Architecture du Projet

```text
.
├── app.py                  # Point d'entrée principal (Navigation)
├── requirements.txt        # Dépendances du projet
├── Notebook_AlphaInfera.ipynb # Recherche, EDA et entraînement du modèle
├── assets/                 # Design system (CSS, thèmes)
├── models/                 # Artefacts du modèle et données de base
│   ├── best_model_rf.joblib
│   ├── features.json
│   └── global_stats.json
├── pages/                  # Modules de l'application Streamlit
│   ├── accueil.py
│   ├── predicteur.py
│   ├── dashboard.py
│   ├── spatial.py
│   └── apropos.py
└── utils/                  # Logique métier et visualisations
    ├── data.py             # Chargement, API Open-Meteo, calculs
    └── charts.py           # Création de graphiques Plotly
```

##  Détails Techniques

### Modèle Prédictif
Le modèle retenu est un **Random Forest (RF) Optimisé** par recherche sur grille (Grid Search).

- **Performance** :
  - **MAE (Mean Absolute Error)** : 0.0503
  - **R² (Coefficient de détermination)** : 0.9994
  - **MAE CV (Validation Croisée)** : 0.076 ± 0.002
- **Features Clés** : Absence de pluie (`is_no_rain`), Saison sèche (`is_dry_season`), Température moyenne, Précipitations cumulées.

### Sources de Données
- **Données historiques** : Dataset IndabaX Cameroon 2026 (87 240 observations).
- **Météo temps réel** : [Open-Meteo API](https://open-meteo.com).
- **Référence Santé** : Lignes directrices de l'OMS (Seuil annuel : 15 µg/m³).


---
*Développé dans le cadre du Hackathon IndabaX Cameroon 2026.*
