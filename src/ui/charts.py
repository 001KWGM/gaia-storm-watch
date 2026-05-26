import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from src.ui.branding import GAIA_DARK, GAIA_GREY, GAIA_LIGHT_GREY, GAIA_BG, GAIA_GOLD


def _base_layout(fig, height=520):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.63)",
        font=dict(color=GAIA_DARK, size=12),
        margin=dict(l=46, r=28, t=52, b=52),
        legend=dict(orientation="h", yanchor="bottom", y=-0.24, xanchor="center", x=0.5),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(45,58,76,0.12)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(45,58,76,0.12)", zeroline=False)
    return fig


def storm_timeline(df: pd.DataFrame, hub_label: str):
    g = df.sort_values("timestamp_awst").copy()
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
        subplot_titles=("Wind and pressure", "Rainfall", "Wave conditions", "Observed water level / residual indicator"),
        specs=[[{"secondary_y": True}], [{}], [{}], [{}]],
    )
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wind_gust_kmh"], name="Wind gust (km/h)", line=dict(color=GAIA_DARK, width=2)), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["air_pressure_hpa"], name="Pressure (hPa)", line=dict(color=GAIA_GREY, width=1.5, dash="dot")), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Bar(x=g["timestamp_awst"], y=g["rainfall_mm"], name="Rainfall (mm / interval)", marker_color=GAIA_LIGHT_GREY), row=2, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wave_hs_m"], name="Hs (m)", line=dict(color=GAIA_GOLD, width=2.4)), row=3, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["wave_hmax_m"], name="Hmax (m)", line=dict(color=GAIA_GREY, width=1.4, dash="dash")), row=3, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["water_level_m"], name="Water level (m)", line=dict(color=GAIA_DARK, width=2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=g["timestamp_awst"], y=g["water_level_residual_m"], name="Residual indicator (m)", line=dict(color=GAIA_GOLD, width=1.5)), row=4, col=1)
    fig.update_layout(title=f"{hub_label} — storm event visualisation")
    fig.update_yaxes(title_text="km/h", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="hPa", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="mm", row=2, col=1)
    fig.update_yaxes(title_text="m / s", row=3, col=1)
    fig.update_yaxes(title_text="m", row=4, col=1)
    return _base_layout(fig, height=790)


def compare_hubs(df: pd.DataFrame, metric: str, label: str):
    agg = df.groupby("hub", as_index=False)[metric].max(numeric_only=True)
    fig = px.bar(agg, x="hub", y=metric, text=metric, title=f"Highest displayed {label} by hub")
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
            if col in g and pd.to_numeric(g[col], errors="coerce").notna().any():
                s = pd.to_numeric(g[col], errors="coerce")
                idx = s.idxmax()
                rows.append({"hub": hub, "metric": name, "time": g.loc[idx, "timestamp_awst"], "value": s.loc[idx]})
    peak = pd.DataFrame(rows)
    if peak.empty:
        return go.Figure()
    fig = px.scatter(peak, x="time", y="hub", color="metric", size=peak["value"].abs() + 0.1,
                     title="Timing of highest displayed values by hub")
    return _base_layout(fig, height=430)


def event_phase_ribbon(df: pd.DataFrame):
    g = df.copy()
    g["timestamp_awst"] = pd.to_datetime(g["timestamp_awst"], errors="coerce")
    # Mean-normalised composite index for storytelling only.
    parts = []
    for col in ["wave_hs_m", "wind_gust_kmh", "rainfall_mm", "water_level_residual_m"]:
        if col in g:
            s = pd.to_numeric(g[col], errors="coerce")
            if s.notna().any() and s.max() != s.min():
                parts.append((s - s.min()) / (s.max() - s.min()))
    if not parts:
        return go.Figure()
    g["event_index"] = pd.concat(parts, axis=1).mean(axis=1)
    agg = g.groupby("timestamp_awst", as_index=False)["event_index"].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=agg["timestamp_awst"], y=agg["event_index"], fill="tozeroy", mode="lines", name="Relative event expression", line=dict(color=GAIA_GOLD, width=2)))
    fig.update_yaxes(title="Relative index", range=[0, max(1, float(agg["event_index"].max()) * 1.1)])
    fig.update_xaxes(title="Time (AWST)")
    fig.update_layout(title="Event-shape overview across displayed hubs")
    return _base_layout(fig, height=330)


def coverage_heatmap(coverage: pd.DataFrame):
    if coverage.empty:
        return go.Figure()
    fig = px.imshow(
        coverage.pivot(index="dataset", columns="hub", values="coverage_percent"),
        text_auto=True,
        aspect="auto",
        title="Displayed data coverage by hub and dataset (%)",
        color_continuous_scale=[[0, "#ABB9BD"], [1, "#2D3A4C"]],
    )
    fig.update_layout(coloraxis_showscale=False)
    return _base_layout(fig, height=380)
