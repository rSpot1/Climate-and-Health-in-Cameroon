"""
utils/charts.py — Visualisations Plotly premium cohérentes avec le design system
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Thème global ──────────────────────────────────────────────────────────────
FONT_SANS = "IBM Plex Sans, Inter, system-ui, sans-serif"
FONT_MONO = "IBM Plex Mono, monospace"

BG_BASE    = "rgba(0,0,0,0)"
BG_CARD    = "#21262d"
GRID_COLOR = "#21262d"
TICK_COLOR = "#30363d"
TEXT_SEC   = "#8b949e"
TEXT_PRI   = "#e6edf3"
BORDER     = "#30363d"

LAYOUT = dict(
    paper_bgcolor=BG_BASE,
    plot_bgcolor=BG_BASE,
    font=dict(family=FONT_SANS, color=TEXT_SEC, size=11),
    margin=dict(l=0, r=0, t=36, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font_size=11),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=TICK_COLOR, tickcolor=TICK_COLOR,
               zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=TICK_COLOR, tickcolor=TICK_COLOR,
               zerolinecolor=GRID_COLOR),
    hoverlabel=dict(bgcolor="#1c2431", bordercolor=BORDER,
                    font=dict(family=FONT_MONO, size=12, color=TEXT_PRI)),
)

RISK_COLORS = {
    "Faible":     "#3fb950",
    "Modere":     "#d29922",
    "Eleve":      "#f0883e",
    "Tres eleve": "#da3633",
}
ACCENT = "#f0a500"
BLUE   = "#388bfd"
GREEN  = "#3fb950"
RED    = "#da3633"
PURPLE = "#bc8cff"

PM25_COLORSCALE = [
    [0.00, "#3fb950"],
    [0.35, "#d29922"],
    [0.60, "#f0883e"],
    [1.00, "#da3633"],
]


def _apply(fig: go.Figure, title: str = "", height: int = 320) -> go.Figure:
    fig.update_layout(
        **LAYOUT,
        height=height,
        title=dict(text=title, font=dict(size=13, color=TEXT_PRI, family=FONT_SANS),
                   x=0, xanchor="left", pad=dict(l=0)),
    )
    return fig


# ── Carte scatter mapbox ──────────────────────────────────────────────────────
def risk_map(df: pd.DataFrame, height: int = 460, pm25_col: str = "pm25_moy") -> go.Figure:
    df = df.copy()
    df["_pm25"] = df[pm25_col]
    df["_size"] = df.get("pm25_p95", df["_pm25"] * 1.4)
    df["_label"] = df.apply(lambda r: (
        f"<b style='font-size:13px'>{r['city']}</b><br>"
        f"<span style='color:#8b949e'>Région :</span> {r['region']}<br>"
        f"<span style='color:#8b949e'>PM2.5 prédit :</span> <b style='color:#f0a500'>{r['_pm25']:.1f} µg/m³</b><br>"
        f"<span style='color:#8b949e'>P95 :</span> {r.get('pm25_p95', r['_pm25']*1.4):.1f} µg/m³<br>"
        f"<span style='color:#8b949e'>Stagnation :</span> {r.get('jours_stagnation', '—')} j/an"
    ), axis=1)

    fig = px.scatter_mapbox(
        df, lat="latitude", lon="longitude",
        color="_pm25", size="_size",
        hover_name="city",
        custom_data=["_label"],
        color_continuous_scale=PM25_COLORSCALE,
        range_color=[df["_pm25"].min() * 0.8, df["_pm25"].max() * 1.1],
        size_max=24, zoom=4.8, height=height,
        mapbox_style="carto-darkmatter",
    )
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    fig.update_coloraxes(
        colorbar=dict(
            title=dict(text="PM2.5<br>µg/m³", font=dict(size=10, color=TEXT_SEC)),
            tickfont=dict(size=10, color=TEXT_SEC, family=FONT_MONO),
            thickness=10, len=0.5, x=1.0,
            bgcolor="rgba(22,27,34,0.85)",
            bordercolor=BORDER, borderwidth=1,
        )
    )
    fig.update_layout(
        paper_bgcolor=BG_BASE,
        margin=dict(l=0, r=0, t=0, b=0),
        hoverlabel=dict(bgcolor="#1c2431", bordercolor=BORDER,
                        font=dict(family=FONT_MONO, size=12, color=TEXT_PRI)),
    )
    return fig


# ── Bar chart villes ──────────────────────────────────────────────────────────
def city_bar(df: pd.DataFrame, title: str = "", pm25_col: str = "pm25_moy",
             height: int = 340) -> go.Figure:
    df = df.sort_values(pm25_col, ascending=True)
    colors = [
        "#da3633" if v > 25 else "#f0883e" if v > 20 else "#d29922" if v > 15 else "#3fb950"
        for v in df[pm25_col]
    ]
    fig = go.Figure(go.Bar(
        x=df[pm25_col], y=df["city"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>PM2.5 : %{x:.1f} µg/m³<extra></extra>",
        text=df[pm25_col].round(1).astype(str) + " µg/m³",
        textposition="outside",
        textfont=dict(family=FONT_MONO, size=10, color=TEXT_SEC),
    ))
    # Ligne OMS
    fig.add_vline(x=15, line=dict(color="rgba(255,255,255,0.25)", dash="dot", width=1.5),
                  annotation_text="OMS 15", annotation_font_size=9,
                  annotation_font_color="#6e7681",
                  annotation_position="top right")
    return _apply(fig, title, height)


# ── Gauge PM2.5 ───────────────────────────────────────────────────────────────
def pm25_gauge(value: float, title: str = "PM2.5 prédit") -> go.Figure:
    if value > 25:   color, level = "#da3633", "Très élevé"
    elif value > 20: color, level = "#f0883e", "Élevé"
    elif value > 15: color, level = "#d29922", "Modéré"
    else:            color, level = "#3fb950", "Bon"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=" µg/m³", font=dict(size=13, family=FONT_MONO, color=TEXT_PRI)),
        title=dict(text=f"<b>{title}</b><br><span style='font-size:.8em;color:{color}'>{level}</span>",
                   font=dict(size=13, family=FONT_SANS, color=TEXT_SEC)),
        gauge=dict(
            axis=dict(range=[0, 45], tickwidth=1, tickcolor=TICK_COLOR,
                      tickfont=dict(size=9, color=TEXT_SEC, family=FONT_MONO),
                      nticks=10),
            bar=dict(color=color, thickness=0.22),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[0,  15], color="rgba(63,185,80,0.08)"),
                dict(range=[15, 20], color="rgba(210,153,34,0.08)"),
                dict(range=[20, 25], color="rgba(240,136,62,0.08)"),
                dict(range=[25, 45], color="rgba(218,54,51,0.08)"),
            ],
            threshold=dict(line=dict(color="rgba(255,255,255,0.3)", width=2),
                           thickness=0.8, value=15),
        ),
    ))
    fig.update_layout(
        paper_bgcolor=BG_BASE,
        font=dict(family=FONT_SANS, color=TEXT_SEC),
        margin=dict(l=20, r=20, t=60, b=20),
        height=220,
    )
    return fig


def pm25_gauge_dashboard(value: float, city: str) -> go.Figure:
    return pm25_gauge(value, f"{city}")


# ── Série temporelle régionale ────────────────────────────────────────────────
def regional_timeseries(df_ts: pd.DataFrame, metric: str = "pm25_moy",
                         height: int = 340) -> go.Figure:
    fig = go.Figure()
    regions = df_ts["region"].unique()

    palette = [ACCENT, BLUE, GREEN, RED, PURPLE,
               "#79c0ff", "#56d364", "#ff7b72", "#ffa657", "#d2a8ff"]

    for i, reg in enumerate(regions):
        sub = df_ts[df_ts["region"] == reg].sort_values("date")
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub[metric],
            name=reg, mode="lines+markers",
            line=dict(width=2, color=color),
            marker=dict(size=5, color=color),
            hovertemplate=f"<b>{reg}</b><br>%{{x|%b %Y}}<br>PM2.5 : %{{y:.1f}} µg/m³<extra></extra>",
        ))

    # Seuil OMS
    if metric == "pm25_moy":
        fig.add_hline(y=15, line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1.5),
                      annotation_text="Seuil OMS 15 µg/m³",
                      annotation_font_size=9, annotation_font_color="#6e7681",
                      annotation_position="bottom right")

    fig.update_xaxes(tickformat="%b %Y", tickangle=-30, tickfont=dict(size=9))
    fig.update_yaxes(title_text="PM2.5 µg/m³" if metric == "pm25_moy" else metric,
                     title_font_size=10)
    return _apply(fig, "", height)


# ── Heatmap mensuelle ─────────────────────────────────────────────────────────
def region_month_heatmap(df_ts: pd.DataFrame, height: int = 320) -> go.Figure:
    if "month_label" not in df_ts.columns:
        df_ts = df_ts.copy()
        df_ts["month_label"] = pd.to_datetime(df_ts["date"]).dt.strftime("%b")

    pivot = df_ts.pivot_table(index="region", columns="month_label",
                               values="pm25_moy", aggfunc="mean")
    month_order = ["Jan","Fév","Mar","Avr","Mai","Juin",
                   "Juil","Aoû","Sep","Oct","Nov","Déc"]
    cols = [c for c in month_order if c in pivot.columns]
    pivot = pivot[cols]

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=PM25_COLORSCALE,
        hovertemplate="<b>%{y}</b><br>%{x}<br>PM2.5 : %{z:.1f} µg/m³<extra></extra>",
        colorbar=dict(title=dict(text="µg/m³", font=dict(size=10, color=TEXT_SEC)),
                      tickfont=dict(size=9, color=TEXT_SEC, family=FONT_MONO),
                      thickness=10),
    ))
    return _apply(fig, "", height)


# ── Scatter stagnation ────────────────────────────────────────────────────────
def stagnation_scatter(df: pd.DataFrame, height: int = 320) -> go.Figure:
    if "jours_stagnation" not in df.columns:
        return go.Figure()

    colors = [
        "#da3633" if v > 25 else "#f0883e" if v > 20 else "#d29922" if v > 15 else "#3fb950"
        for v in df["pm25_moy"]
    ]
    fig = go.Figure(go.Scatter(
        x=df["jours_stagnation"], y=df["pm25_moy"],
        mode="markers+text",
        marker=dict(size=10, color=colors, line=dict(width=1, color="rgba(255,255,255,0.2)")),
        text=df["city"],
        textposition="top center",
        textfont=dict(size=9, color=TEXT_SEC, family=FONT_SANS),
        hovertemplate="<b>%{text}</b><br>Stagnation : %{x} j/an<br>PM2.5 : %{y:.1f} µg/m³<extra></extra>",
    ))
    fig.add_hline(y=15, line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1.5),
                  annotation_text="OMS 15", annotation_font_size=9,
                  annotation_font_color="#6e7681", annotation_position="right")
    fig.update_xaxes(title_text="Jours de stagnation / an", title_font_size=10)
    fig.update_yaxes(title_text="PM2.5 moyen (µg/m³)", title_font_size=10)
    return _apply(fig, "", height)


# ── Graphe prévisions PM2.5 (ligne + aire) ────────────────────────────────────
def forecast_line(dates: list, values: list, city: str, height: int = 280) -> go.Figure:
    colors = [
        "#da3633" if v > 25 else "#f0883e" if v > 20 else "#d29922" if v > 15 else "#3fb950"
        for v in values
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values,
        mode="lines+markers",
        name="PM2.5 prédit",
        line=dict(color=ACCENT, width=2.5),
        marker=dict(size=8, color=colors, line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
        fill="tozeroy",
        fillcolor="rgba(240,165,0,0.07)",
        hovertemplate="<b>%{x|%d %b}</b><br>PM2.5 : %{y:.1f} µg/m³<extra></extra>",
    ))
    fig.add_hline(y=15, line=dict(color="rgba(255,255,255,0.2)", dash="dot", width=1.5),
                  annotation_text="OMS 15 µg/m³",
                  annotation_font_size=9, annotation_font_color="#6e7681",
                  annotation_position="top right")
    fig.update_xaxes(tickformat="%d %b", tickangle=-30, tickfont=dict(size=9))
    fig.update_yaxes(title_text="µg/m³", title_font_size=10, rangemode="tozero")
    return _apply(fig, f"Prévisions PM2.5 — {city}", height)


# ── Graphe météo (courbe temp, vent) ──────────────────────────────────────────
def meteo_lines(dates: list, temp_max: list, temp_min: list,
                wind: list, height: int = 260) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=dates, y=temp_max, name="Temp. max (°C)",
        mode="lines+markers", line=dict(color="#f0883e", width=2),
        marker=dict(size=5), fill="tonexty",
        hovertemplate="%{x|%d %b}<br>Temp. max : %{y:.0f}°C<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=dates, y=temp_min, name="Temp. min (°C)",
        mode="lines", line=dict(color="#388bfd", width=1.5, dash="dot"),
        fillcolor="rgba(240,136,62,0.06)",
        hovertemplate="%{x|%d %b}<br>Temp. min : %{y:.0f}°C<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=dates, y=wind, name="Vent max (km/h)",
        mode="lines", line=dict(color=PURPLE, width=1.5, dash="dashdot"),
        hovertemplate="%{x|%d %b}<br>Vent : %{y:.0f} km/h<extra></extra>",
    ), secondary_y=True)

    fig.update_yaxes(title_text="Température (°C)", secondary_y=False,
                     title_font_size=10, gridcolor=GRID_COLOR)
    fig.update_yaxes(title_text="Vent (km/h)", secondary_y=True,
                     title_font_size=10, showgrid=False)
    fig.update_xaxes(tickformat="%d %b", tickangle=-30, tickfont=dict(size=9))
    fig.update_layout(**LAYOUT, height=height, title="")
    return fig
