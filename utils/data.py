"""
utils/data.py — Chargement des données, modèle, et API temps réel
"""
from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent / "models"


# ── Chargement des artefacts ──────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model():
    """Charge le modèle RF Optimisé."""
    try:
        import joblib
        model = joblib.load(MODELS_DIR / "best_model_rf.joblib")
        return model
    except Exception as e:
        st.warning(f"Modèle non trouvé ({e}). Mode démo activé.")
        return None


@st.cache_data(show_spinner=False)
def load_features() -> list[str]:
    path = MODELS_DIR / "features.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return [
        "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
        "precipitation_sum", "wind_speed_10m_max", "wind_gusts_10m_max",
        "shortwave_radiation_sum", "et0_fao_evapotranspiration", "sunshine_ratio",
        "temp_amplitude", "is_no_wind", "is_no_rain", "is_dry_season",
        "month_sin", "month_cos", "day_of_year",
        "temp_lag1", "temp_lag7", "wind_lag1", "temp_roll7",
        "latitude", "longitude", "region_enc", "city_enc",
    ]


@st.cache_data(show_spinner=False)
def load_global_stats() -> dict:
    path = MODELS_DIR / "global_stats.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    # Valeurs de démo issues du notebook
    return {
        "n_villes": 40,
        "n_regions": 10,
        "n_observations": 87240,
        "periode_debut": "2020-01-01",
        "periode_fin": "2025-12-20",
        "pm25_national_moy": 18.40,
        "pm25_national_p95": 26.80,
        "seuil_oms": 15.0,
        "best_model_name": "RF Optimisé (GridSearch)",
        "best_model_mae": 0.0503,
        "best_model_r2": 0.9994,
        "lat_min": 2.2,
        "lat_max": 13.1,
    }


@st.cache_data(show_spinner=False)
def load_city_profiles() -> pd.DataFrame:
    path = MODELS_DIR / "city_profiles.csv"
    if path.exists():
        return pd.read_csv(path)
    # Jeu de démo
    return pd.DataFrame({
        "city": ["Maroua", "Garoua", "Ngaoundere", "Yaounde", "Douala",
                 "Bertoua", "Bafoussam", "Ebolowa", "Kribi", "Buea"],
        "region": ["Extreme-Nord", "Nord", "Adamaoua", "Centre", "Littoral",
                   "Est", "Ouest", "Sud", "Sud", "Sud-Ouest"],
        "latitude":  [10.60, 9.30, 7.32, 3.87, 4.05, 4.58, 5.47, 2.90, 2.94, 4.15],
        "longitude": [14.33, 13.39, 13.58, 11.52, 9.70, 13.69, 10.42, 11.15, 9.90, 9.24],
        "temp_moy":  [32.4, 30.8, 22.8, 23.8, 25.2, 23.9, 20.5, 24.1, 26.3, 24.8],
        "precip_moy":[0.1,  0.2,  0.5,  2.1,  4.8,  1.8,  2.9,  3.2,  5.1,  6.0],
        "vent_moy":  [16.1, 13.3, 12.4, 11.4, 10.7, 10.2, 12.3, 11.1, 9.8,  12.4],
        "radiation_moy":[20.9,20.4,19.9,17.5,16.2,18.6,19.2,16.5,16.8,16.6],
        "et0_moy":   [6.26, 5.45, 4.60, 3.67, 3.32, 3.91, 3.97, 3.39, 3.44, 3.44],
    })


@st.cache_data(show_spinner=False)
def load_risk_table() -> pd.DataFrame:
    path = MODELS_DIR / "risk_table.csv"
    if path.exists():
        return pd.read_csv(path)
    # Démo
    cities = load_city_profiles()
    pm25_demo = [26.8, 23.2, 19.4, 16.8, 14.2, 17.9, 15.6, 13.8, 12.4, 14.1]
    risk_df = cities[["city", "region", "latitude", "longitude"]].copy()
    risk_df["pm25_moy"] = pm25_demo
    risk_df["pm25_p95"] = [v * 1.4 for v in pm25_demo]
    risk_df["jours_stagnation"] = [68, 54, 38, 22, 12, 28, 18, 10, 8, 14]
    risk_df["jours_harmattan"] = [0.35, 0.30, 0.18, 0.05, 0.02, 0.08, 0.04, 0.02, 0.01, 0.03]
    def niveau(v):
        if v > 25: return "Tres eleve"
        if v > 20: return "Eleve"
        if v > 16: return "Modere"
        return "Faible"
    risk_df["niveau_risque"] = risk_df["pm25_moy"].apply(niveau)
    return risk_df


# ── API Open-Meteo — données météo temps réel ─────────────────────────────────
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

OPEN_METEO_PARAMS = [
    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
    "apparent_temperature_max", "apparent_temperature_min", "apparent_temperature_mean",
    "precipitation_sum", "rain_sum",
    "wind_speed_10m_max", "wind_gusts_10m_max",
    "shortwave_radiation_sum", "et0_fao_evapotranspiration",
    "sunshine_duration", "daylight_duration",
]


@st.cache_data(ttl=1800, show_spinner=False)  # cache 30 min
def fetch_realtime_meteo(lat: float, lon: float, days: int = 7) -> Optional[pd.DataFrame]:
    """Appel API Open-Meteo pour récupérer les données météo temps réel."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(OPEN_METEO_PARAMS),
            "timezone": "Africa/Douala",
            "forecast_days": days,
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data["daily"])
        df["time"] = pd.to_datetime(df["time"])
        return df
    except Exception as e:
        return None


def build_feature_row(meteo_row: pd.Series, lat: float, lon: float,
                       region_enc: int, city_enc: int) -> pd.DataFrame:
    """
    Construit une ligne de features à partir d'une ligne météo brute
    (compatible avec la liste FEATURES du modèle).
    """
    month = meteo_row.get("time", pd.Timestamp.now()).month if hasattr(
        meteo_row.get("time", None), "month") else pd.Timestamp.now().month
    doy   = meteo_row.get("time", pd.Timestamp.now()).dayofyear if hasattr(
        meteo_row.get("time", None), "dayofyear") else pd.Timestamp.now().dayofyear

    t_mean = float(meteo_row.get("temperature_2m_mean", 25.0) or 25.0)
    t_max  = float(meteo_row.get("temperature_2m_max",  30.0) or 30.0)
    t_min  = float(meteo_row.get("temperature_2m_min",  20.0) or 20.0)
    precip = float(meteo_row.get("precipitation_sum",    0.0) or 0.0)
    wind   = float(meteo_row.get("wind_speed_10m_max",  12.0) or 12.0)
    gusts  = float(meteo_row.get("wind_gusts_10m_max",  18.0) or 18.0)
    rad    = float(meteo_row.get("shortwave_radiation_sum", 18.0) or 18.0)
    et0    = float(meteo_row.get("et0_fao_evapotranspiration", 4.0) or 4.0)
    sun    = float(meteo_row.get("sunshine_duration",  28000) or 28000)
    day    = float(meteo_row.get("daylight_duration",  44000) or 44000)

    sunshine_ratio = min(sun / max(day, 1), 1.0)
    temp_amplitude = t_max - t_min
    is_no_wind     = int(wind < 5)
    is_no_rain     = int(precip < 0.1)
    is_dry_season  = int(month in [11, 12, 1, 2, 3])

    row = {
        "temperature_2m_mean":          t_mean,
        "temperature_2m_max":           t_max,
        "temperature_2m_min":           t_min,
        "precipitation_sum":            precip,
        "wind_speed_10m_max":           wind,
        "wind_gusts_10m_max":           gusts,
        "shortwave_radiation_sum":      rad,
        "et0_fao_evapotranspiration":   et0,
        "sunshine_ratio":               sunshine_ratio,
        "temp_amplitude":               temp_amplitude,
        "is_no_wind":                   is_no_wind,
        "is_no_rain":                   is_no_rain,
        "is_dry_season":                is_dry_season,
        "month_sin":                    np.sin(2 * np.pi * month / 12),
        "month_cos":                    np.cos(2 * np.pi * month / 12),
        "day_of_year":                  doy,
        "temp_lag1":                    t_mean,
        "temp_lag7":                    t_mean,
        "wind_lag1":                    wind,
        "temp_roll7":                   t_mean,
        "latitude":                     lat,
        "longitude":                    lon,
        "region_enc":                   region_enc,
        "city_enc":                     city_enc,
    }
    return pd.DataFrame([row])


def predict_pm25(model, feature_row: pd.DataFrame, features: list[str]) -> float:
    """Lance la prédiction PM2.5 avec le modèle chargé ou retourne un proxy calculé."""
    if model is not None:
        try:
            X = feature_row[features]
            return float(model.predict(X)[0])
        except Exception:
            pass
    # # Proxy de secours (formule du notebook)
    # r = feature_row.iloc[0]
    # val = (0.35 * r.get("temperature_2m_mean", 25)
    #        + 0.25 * r.get("shortwave_radiation_sum", 18)
    #        + 0.20 * r.get("et0_fao_evapotranspiration", 4)
    #        + 8.0  * r.get("is_no_wind", 0)
    #        + 5.0  * r.get("is_no_rain", 0)
    #        + 4.0  * r.get("is_dry_season", 0))
    # return max(float(val), 7.5)


def pm25_level(value: float) -> tuple[str, str]:
    """Retourne (label, css_class) selon le niveau PM2.5."""
    if value > 25:  return "Très élevé", "critical"
    if value > 20:  return "Élevé",      "high"
    if value > 16:  return "Modéré",     "medium"
    return "Faible", "low"


def oms_ratio(value: float, seuil: float = 15.0) -> float:
    return round(value / seuil, 2)
