"""
utils/charts.py — Helpers de visualisation Plotly avec thème cohérent
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Thème global ──────────────────────────────────────────────────────────────
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans, sans-serif", color="#8b949e", size=11),
    margin=dict(l=0, r=0, t=32, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font_size=11),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d",
               zerolinecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#30363d",
               zerolinecolor="#30363d"),
    hoverlabel=dict(bgcolor="#1c2431", bordercolor="#30363d",
                    font=dict(family="IBM Plex Mono, monospace", size=12)),
)

RISK_COLORS = {
    "Faible":      "#3fb950",
    "Modere":      "#d29922",
    "Eleve":       "#f0883e",
    "Tres eleve":  "#da3633",
}

ACCENT = "#f0a500"
BLUE   = "#388bfd"
GREEN  = "#3fb950"
RED    = "#da3633"

# Lignes OMS en rgba() — Plotly n'accepte PAS les hex à 8 chiffres (#rrggbbaa)
_OMS_LINE = "rgba(255,255,255,0.19)"
_OMS_ANN  = "#6e7681"
_THRESH   = "rgba(255,255,255,0.25)"


def _fig(fig: go.Figure, title: str = "", height: int = 320) -> go.Figure:
    fig.update_layout(**LAYOUT, title=dict(
        text=title, font=dict(size=13, color="#e6edf3", family="IBM Plex Sans"),
        x=0, xanchor="left", pad=dict(l=0),
    ), height=height)
    return fig


# ── Carte scatter mapbox ──────────────────────────────────────────────────────
def risk_map(df: pd.DataFrame, height: int = 460) -> go.Figure:
    df = df.copy()
    df["label"] = df.apply(
        lambda r: (
            f"<b>{r['city']}</b><br>"
            f"Région : {r['region']}<br>"
            f"PM2.5 moy : {r['pm25_moy']:.1f} µg/m³<br>"
            f"PM2.5 P95 : {r.get('pm25_p95', r['pm25_moy']*1.4):.1f} µg/m³<br>"
            f"Stagnation : {r.get('jours_stagnation', '—')} j/an"
        ),
        axis=1,
    )
    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude",
        color="pm25_moy", size="pm25_p95",
        hover_name="city",
        custom_data=["label"],
        color_continuous_scale=[
            [0.0,  "#3fb950"],
            [0.45, "#d29922"],
            [0.70, "#f0883e"],
            [1.0,  "#da3633"],
        ],
        size_max=22, zoom=4.8, height=height,
        mapbox_style="carto-darkmatter",
    )
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    fig.update_coloraxes(
        colorbar=dict(
            title="PM2.5<br>µg/m³", thickness=10, len=0.7,
            tickfont=dict(family="IBM Plex Mono", size=10, color="#8b949e"),
            title_font=dict(size=10, color="#8b949e"),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(family="IBM Plex Sans"),
    )
    return fig


# ── Série temporelle multi-région ─────────────────────────────────────────────
def regional_timeseries(df_ts: pd.DataFrame, y_col: str = "pm25_moy",
                         title: str = "", height: int = 320) -> go.Figure:
    fig = go.Figure()
    palette = [ACCENT, BLUE, GREEN, RED, "#bc8cff", "#79c0ff", "#56d364",
               "#ff7b72", "#ffa657", "#f0883e", "#d29922", "#8b949e"]
    regions = df_ts["region"].unique() if "region" in df_ts.columns else []
    for i, reg in enumerate(regions):
        sub = df_ts[df_ts["region"] == reg].sort_values("date")
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub[y_col], mode="lines", name=reg,
            line=dict(color=palette[i % len(palette)], width=1.5),
            hovertemplate=(
                f"<b>{reg}</b><br>%{{x|%d %b %Y}}<br>"
                "PM2.5 : %{y:.2f} µg/m³<extra></extra>"
            ),
        ))
    if len(df_ts):
        fig.add_hline(y=15, line=dict(color=_OMS_LINE, width=1, dash="dot"),
                      annotation_text="Seuil OMS", annotation_font_size=10,
                      annotation_font_color=_OMS_ANN)
    return _fig(fig, title, height)


# ── Bar chart comparaison villes ──────────────────────────────────────────────
def city_bar(df: pd.DataFrame, x_col: str = "pm25_moy",
              y_col: str = "city", title: str = "", height: int = 340) -> go.Figure:
    df = df.sort_values(x_col)
    colors = [RISK_COLORS.get(n, ACCENT)
              for n in df.get("niveau_risque", ["Faible"] * len(df))]
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col], orientation="h",
        marker=dict(color=colors, cornerradius=3),
        hovertemplate="<b>%{y}</b><br>PM2.5 : %{x:.2f} µg/m³<extra></extra>",
    ))
    fig.add_vline(x=15, line=dict(color=_OMS_LINE, width=1, dash="dot"),
                  annotation_text="OMS", annotation_font_size=10,
                  annotation_font_color=_OMS_ANN, annotation_position="top right")
    return _fig(fig, title, height)


# ── Gauge PM2.5 — prédicteur ──────────────────────────────────────────────────
def pm25_gauge(value: float, title: str = "PM2.5 prédit", height: int = 240) -> go.Figure:
    if value <= 15:    bar_color = GREEN
    elif value <= 20:  bar_color = "#d29922"
    elif value <= 25:  bar_color = "#f0883e"
    else:              bar_color = RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={
            "reference": 15, "valueformat": ".2f",
            "font": {"size": 13, "family": "IBM Plex Mono"},
            "increasing": {"color": RED}, "decreasing": {"color": GREEN},
        },
        number={
            "suffix": " µg/m³", "valueformat": ".2f",
            "font": {"size": 28, "family": "IBM Plex Mono", "color": "#e6edf3"},
        },
        title={"text": title,
               "font": {"size": 12, "color": "#8b949e", "family": "IBM Plex Sans"}},
        gauge={
            "axis": {
                "range": [0, 35], "tickwidth": 1,
                "tickcolor": "#30363d",
                "tickfont": {"size": 9, "color": "#6e7681"},
                "tickvals": [0, 5, 10, 15, 20, 25, 30, 35],
            },
            "bar":  {"color": bar_color, "thickness": 0.25},
            "bgcolor": "#161b22",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  15], "color": "rgba(63,185,80,0.08)"},
                {"range": [15, 20], "color": "rgba(210,153,34,0.08)"},
                {"range": [20, 25], "color": "rgba(240,136,62,0.08)"},
                {"range": [25, 35], "color": "rgba(218,54,51,0.08)"},
            ],
            "threshold": {"line": {"color": _THRESH, "width": 2}, "value": 15},
        },
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=height,
                      margin=dict(l=10, r=10, t=40, b=10),
                      font=dict(family="IBM Plex Sans"))
    return fig


# ── Gauge PM2.5 — dashboard (jauge pro avec arcs et annotation) ───────────────
def pm25_gauge_dashboard(value: float, region: str = "", height: int = 260) -> go.Figure:
    """Jauge professionnelle pour le tableau de bord."""
    if value <= 15:
        bar_color, level_label, level_color = GREEN, "Bon", GREEN
    elif value <= 20:
        bar_color, level_label, level_color = "#d29922", "Modéré", "#d29922"
    elif value <= 25:
        bar_color, level_label, level_color = "#f0883e", "Élevé", "#f0883e"
    else:
        bar_color, level_label, level_color = RED, "Critique", RED

    oms_ratio = value / 15.0
    title_text = (
        f"<b style='color:#e6edf3'>{region}</b><br>"
        f"<span style='color:{level_color}'>{level_label}</span>"
        f"<span style='color:#6e7681;font-size:10px'> · × {oms_ratio:.2f} OMS</span>"
    )

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={
            "suffix": " µg/m³", "valueformat": ".1f",
            "font": {"size": 22, "family": "IBM Plex Mono", "color": bar_color},
        },
        title={"text": title_text,
               "font": {"size": 12, "family": "IBM Plex Sans", "color": "#8b949e"}},
        gauge={
            "axis": {
                "range": [0, 35], "tickwidth": 1,
                "tickcolor": "#30363d",
                "tickfont": {"size": 8, "color": "#6e7681"},
                "tickvals": [0, 15, 20, 25, 35],
                "ticktext": ["0", "15 OMS", "20", "25", "35+"],
            },
            "bar": {"color": bar_color, "thickness": 0.30},
            "bgcolor": "#161b22",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  15], "color": "rgba(63,185,80,0.10)"},
                {"range": [15, 20], "color": "rgba(210,153,34,0.10)"},
                {"range": [20, 25], "color": "rgba(240,136,62,0.10)"},
                {"range": [25, 35], "color": "rgba(218,54,51,0.10)"},
            ],
            "threshold": {"line": {"color": _THRESH, "width": 2}, "value": 15},
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(family="IBM Plex Sans"),
    )
    return fig


# ── Heatmap région × mois ─────────────────────────────────────────────────────
def region_month_heatmap(pivot: pd.DataFrame, title: str = "", height: int = 300) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "#3fb950"], [0.4, "#d29922"],
            [0.7, "#f0883e"], [1.0, "#da3633"],
        ],
        hovertemplate="<b>%{y}</b> · Mois %{x}<br>PM2.5 : %{z:.2f} µg/m³<extra></extra>",
        showscale=True,
        colorbar=dict(thickness=10,
                      tickfont=dict(family="IBM Plex Mono", size=9, color="#8b949e"),
                      bgcolor="rgba(0,0,0,0)", borderwidth=0),
    ))
    return _fig(fig, title, height)


# ── Scatter stagnation vs PM2.5 ──────────────────────────────────────────────
def stagnation_scatter(df: pd.DataFrame, height: int = 300) -> go.Figure:
    fig = px.scatter(
        df, x="jours_stagnation", y="pm25_moy",
        color="niveau_risque",
        color_discrete_map=RISK_COLORS,
        hover_name="city",
        size="pm25_p95",
        size_max=14,
        labels={"jours_stagnation": "Jours de stagnation / an",
                "pm25_moy": "PM2.5 moyen (µg/m³)"},
    )
    fig.add_hline(y=15, line=dict(color=_OMS_LINE, width=1, dash="dot"),
                  annotation_text="OMS", annotation_font_size=10,
                  annotation_font_color=_OMS_ANN)
    return _fig(fig, "Stagnation atmosphérique vs PM2.5", height)
