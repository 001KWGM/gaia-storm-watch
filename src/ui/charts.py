import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from src.ui.branding import GAIA_DARK, GAIA_GREY, GAIA_LIGHT_GREY, GAIA_BG, GAIA_GOLD


def _base_layout(fig, height=520):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.55)",
        font=dict(color=GAIA_DARK, size=12),
        margin=dict(l=42, r=26, t=42, b=42),
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(45,58,76,0.12)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(45,58,76,0.12)")
    return fig


def storm_timeline(df: pd.DataFrame, hub_label: str):
    g = df.sort_values("timestamp_awst").copy()
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.045,
        subplot_titles=("Wind and pressure", "Rainfall", "Wave conditions", "Observed water level / residual")
    )
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wind_gust_kmh"], name="Wind gust (km/h)", line=dict(color=GAIA_DARK, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["air_pressure_hpa"], name="Pressure (hPa)", line=dict(color=GAIA_GREY, width=1.5, dash="dot"), yaxis="y2"), row=1, col=1)
    fig.add_trace(go.Bar(x=g["timestamp_awst"], y=g["rainfall_mm"], name="Rainfall (mm / interval)", marker_color=GAIA_LIGHT_GREY), row=2, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wave_hs_m"], name="Hs (m)", line=dict(color=GAIA_GOLD, width=2.4)), row=3, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wave_hmax_m"], name="Hmax (m)", line=dict(color=GAIA_GREY, width=1.4, dash="dash")), row=3, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["water_level_m"], name="Water level (m)", line=dict(color=GAIA_DARK, width=2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["water_level_residual_m"], name="Residual indicator (m)", line=dict(color=GAIA_GOLD, width=1.5)), row=4, col=1)
    fig.update_layout(title=f"{hub_label} — storm event visualisation")
    fig.update_yaxes(title_text="km/h / hPa", row=1, col=1)
    fig.update_yaxes(title_text="mm", row=2, col=1)
    fig.update_yaxes(title_text="m / s", row=3, col=1)
    fig.update_yaxes(title_text="m", row=4, col=1)
    return _base_layout(fig, height=760)


def compare_hubs(df: pd.DataFrame, metric: str, label: str):
    agg = df.groupby("hub", as_index=False)[metric].max(numeric_only=True)
    fig = px.bar(agg, x="hub", y=metric, text=metric, title=f"Highest observed {label} by hub")
    fig.update_traces(marker_color=GAIA_DARK, texttemplate="%{text:.2f}", textposition="outside")
    fig.update_yaxes(title=label)
    return _base_layout(fig, height=440)


def peak_timing_strip(df: pd.DataFrame):
    metrics = {
        "Wave Hs": "wave_hs_m",
        "Wind gust": "wind_gust_kmh",
        "Rainfall": "rainfall_mm",
        "Water residual": "water_level_residual_m",
    }
    rows = []
    for hub, g in df.groupby("hub"):
        for name, col in metrics.items():
            if col in g and g[col].notna().any():
                idx = g[col].astype(float).idxmax()
                rows.append({"hub": hub, "metric": name, "time": g.loc[idx, "timestamp_awst"], "value": g.loc[idx, col]})
    peak = pd.DataFrame(rows)
    if peak.empty:
        return go.Figure()
    fig = px.scatter(peak, x="time", y="hub", color="metric", size=peak["value"].abs() + 0.1,
                     title="When each hub shows its highest observed values")
    return _base_layout(fig, height=420)
