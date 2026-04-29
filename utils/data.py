"""
utils/data.py — Chargement des données, modèle RF AlphaInfera, API Open-Meteo
Le modèle best_model_rf.joblib est toujours présent dans models/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests
import streamlit as st

MODELS_DIR = Path(__file__).parent.parent / "models"


# ── Chargement artefacts ──────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_model():
    """Charge le modèle RF AlphaInfera (toujours présent dans models/)."""
    import joblib
    return joblib.load(MODELS_DIR / "best_model_rf.joblib")


@st.cache_data(show_spinner=False)
def load_features() -> list[str]:
    path = MODELS_DIR / "features.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return [
        "temperature_2m_mean","temperature_2m_max","temperature_2m_min",
        "precipitation_sum","wind_speed_10m_max","wind_gusts_10m_max",
        "shortwave_radiation_sum","et0_fao_evapotranspiration","sunshine_ratio",
        "temp_amplitude","is_no_wind","is_no_rain","is_dry_season",
        "month_sin","month_cos","day_of_year",
        "temp_lag1","temp_lag7","wind_lag1","temp_roll7",
        "latitude","longitude","region_enc","city_enc",
    ]


@st.cache_data(show_spinner=False)
def load_global_stats() -> dict:
    path = MODELS_DIR / "global_stats.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {
        "n_villes": 40, "n_regions": 10, "n_observations": 87240,
        "periode_debut": "2020-01-01", "periode_fin": "2025-12-20",
        "pm25_national_moy": 18.40, "pm25_national_p95": 26.80,
        "seuil_oms": 15.0, "best_model_name": "RF Optimisé (GridSearch)",
        "best_model_mae": 0.0503, "best_model_r2": 0.9994,
        "lat_min": 2.2, "lat_max": 13.1,
    }


@st.cache_data(show_spinner=False)
def load_city_profiles() -> pd.DataFrame:
    path = MODELS_DIR / "city_profiles.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_risk_table() -> pd.DataFrame:
    path = MODELS_DIR / "risk_table.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


# ── API Open-Meteo ────────────────────────────────────────────────────────────

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_PARAMS = [
    "temperature_2m_max","temperature_2m_min","temperature_2m_mean",
    "precipitation_sum","rain_sum",
    "wind_speed_10m_max","wind_gusts_10m_max",
    "shortwave_radiation_sum","et0_fao_evapotranspiration",
    "sunshine_duration","daylight_duration",
]


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_realtime_meteo(lat: float, lon: float, days: int = 7) -> Optional[pd.DataFrame]:
    """Récupère les prévisions météo Open-Meteo (cache 30 min)."""
    try:
        params = {
            "latitude": lat, "longitude": lon,
            "daily": ",".join(OPEN_METEO_PARAMS),
            "timezone": "Africa/Douala",
            "forecast_days": min(days, 16),
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data["daily"])
        df["time"] = pd.to_datetime(df["time"])
        return df
    except Exception:
        return None


def build_feature_row(meteo_row: pd.Series, lat: float, lon: float,
                       region_enc: int, city_enc: int) -> pd.DataFrame:
    """Construit la ligne de features attendue par le modèle RF."""
    ts    = meteo_row.get("time", pd.Timestamp.now())
    month = ts.month     if hasattr(ts, "month")     else pd.Timestamp.now().month
    doy   = ts.dayofyear if hasattr(ts, "dayofyear") else pd.Timestamp.now().dayofyear

    t_mean = float(meteo_row.get("temperature_2m_mean",         25.0) or 25.0)
    t_max  = float(meteo_row.get("temperature_2m_max",          30.0) or 30.0)
    t_min  = float(meteo_row.get("temperature_2m_min",          20.0) or 20.0)
    precip = float(meteo_row.get("precipitation_sum",            0.0) or  0.0)
    wind   = float(meteo_row.get("wind_speed_10m_max",          12.0) or 12.0)
    gusts  = float(meteo_row.get("wind_gusts_10m_max",          18.0) or 18.0)
    rad    = float(meteo_row.get("shortwave_radiation_sum",      18.0) or 18.0)
    et0    = float(meteo_row.get("et0_fao_evapotranspiration",   4.0) or  4.0)
    sun    = float(meteo_row.get("sunshine_duration",          28000) or 28000)
    day    = float(meteo_row.get("daylight_duration",          44000) or 44000)

    sunshine_ratio = min(sun / max(day, 1), 1.0)
    temp_amplitude = t_max - t_min
    is_no_wind     = int(wind < 5)
    is_no_rain     = int(precip < 0.1)
    is_dry_season  = int(month in [11, 12, 1, 2, 3])

    return pd.DataFrame([{
        "temperature_2m_mean":         t_mean,
        "temperature_2m_max":          t_max,
        "temperature_2m_min":          t_min,
        "precipitation_sum":           precip,
        "wind_speed_10m_max":          wind,
        "wind_gusts_10m_max":          gusts,
        "shortwave_radiation_sum":     rad,
        "et0_fao_evapotranspiration":  et0,
        "sunshine_ratio":              sunshine_ratio,
        "temp_amplitude":              temp_amplitude,
        "is_no_wind":                  is_no_wind,
        "is_no_rain":                  is_no_rain,
        "is_dry_season":               is_dry_season,
        "month_sin":                   np.sin(2 * np.pi * month / 12),
        "month_cos":                   np.cos(2 * np.pi * month / 12),
        "day_of_year":                 doy,
        "temp_lag1":                   t_mean,
        "temp_lag7":                   t_mean,
        "wind_lag1":                   wind,
        "temp_roll7":                  t_mean,
        "latitude":                    lat,
        "longitude":                   lon,
        "region_enc":                  region_enc,
        "city_enc":                    city_enc,
    }])


def predict_pm25(model, feature_row: pd.DataFrame, features: list[str]) -> float:
    """Prédiction PM2.5 directe via le modèle RF AlphaInfera."""
    X = feature_row[features]
    return float(model.predict(X)[0])


def get_region_city_enc(city_name: str, cities_df: pd.DataFrame) -> tuple[int, int]:
    """Retourne (region_enc, city_enc) pour une ville donnée."""
    city_list   = cities_df["city"].tolist()
    region_list = sorted(cities_df["region"].unique().tolist())
    city_enc    = city_list.index(city_name) if city_name in city_list else 0
    region      = cities_df[cities_df["city"] == city_name].iloc[0]["region"] \
                  if city_name in city_list else ""
    region_enc  = region_list.index(region) if region in region_list else 0
    return region_enc, city_enc


def predict_city_forecasts(city_name: str, cities_df: pd.DataFrame,
                            model, features: list[str],
                            days: int = 7) -> tuple[list, list]:
    """
    Récupère les données Open-Meteo pour une ville et prédit le PM2.5
    pour chaque jour via le modèle RF.
    Retourne (dates, pm25_predictions).
    """
    row = cities_df[cities_df["city"] == city_name].iloc[0]
    lat, lon = float(row["latitude"]), float(row["longitude"])
    region_enc, city_enc = get_region_city_enc(city_name, cities_df)

    meteo = fetch_realtime_meteo(lat, lon, days=days)
    if meteo is None or len(meteo) == 0:
        return [], []

    dates, preds = [], []
    for _, mrow in meteo.iterrows():
        feat = build_feature_row(mrow, lat, lon, region_enc, city_enc)
        preds.append(predict_pm25(model, feat, features))
        dates.append(mrow["time"])
    return dates, preds


def pm25_level(value: float) -> tuple[str, str]:
    if value > 25: return "Très élevé", "critical"
    if value > 20: return "Élevé",      "high"
    if value > 15: return "Modéré",     "medium"
    return "Bon", "low"


def pm25_color(value: float) -> str:
    if value > 25: return "#da3633"
    if value > 20: return "#f0883e"
    if value > 15: return "#d29922"
    return "#3fb950"


def oms_ratio(value: float, seuil: float = 15.0) -> float:
    return round(value / seuil, 2)
