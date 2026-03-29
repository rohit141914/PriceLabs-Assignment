"""
part3_forecast.py
──────────────────
Part 3 — Forecast Chart Builder

Functions:
    build_forecast(raw_df, years)  – Feb 2022 forecast using linear trend + seasonal index

Method:
    1. Fit a linear trend on annual medians → extrapolate to 2022
    2. Compute a day-of-year seasonal index from the full historical dataset
    3. Predicted price = extrapolated_base × seasonal_index
"""

from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from config import YEAR_COLORS, PLOTLY_LAYOUT, filter_df


def get_forecast_data(raw_df: pd.DataFrame, years: List[int]) -> List[dict]:
    """Return the 28 Feb 2022 daily predictions as a list of dicts for the API."""
    df     = filter_df(raw_df, years)
    annual = df.groupby("Year")["Price"].median().reset_index()
    if len(annual) >= 2:
        slope, intercept, *_ = stats.linregress(annual["Year"], annual["Price"])
    else:
        slope, intercept = 0.0, float(annual["Price"].iloc[0])

    base_2022    = intercept + slope * 2022
    overall_mean = raw_df["Price"].mean()
    seasonal_idx = raw_df.groupby("DayOfYear")["Price"].mean() / overall_mean
    feb_dates    = pd.date_range("2022-02-01", "2022-02-28")
    preds        = (base_2022 * seasonal_idx.reindex(feb_dates.dayofyear).values).round(2)
    fitted       = (intercept + slope * raw_df["Year"]) * seasonal_idx.reindex(raw_df["DayOfYear"].values).values
    residual_std = float(np.nanstd(raw_df["Price"].values - fitted))

    return [
        {
            "date":  d.strftime("%b %d, %Y"),
            "price": float(p),
            "low":   round(float(p) - residual_std, 2),
            "high":  round(float(p) + residual_std, 2),
        }
        for d, p in zip(feb_dates, preds)
        if not np.isnan(p)
    ]


def build_forecast(raw_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df     = filter_df(raw_df, years)
    annual = df.groupby("Year")["Price"].median().reset_index()
    if len(annual) >= 2:
        slope, intercept, *_ = stats.linregress(annual["Year"], annual["Price"])
    else:
        slope, intercept = 0.0, float(annual["Price"].iloc[0])

    base_2022    = intercept + slope * 2022
    overall_mean = raw_df["Price"].mean()
    seasonal_idx = raw_df.groupby("DayOfYear")["Price"].mean() / overall_mean
    feb_dates    = pd.date_range("2022-02-01", "2022-02-28")
    preds        = (base_2022 * seasonal_idx.reindex(feb_dates.dayofyear).values).round(2)

    # Residual-based uncertainty band
    fitted       = (intercept + slope * raw_df["Year"]) * seasonal_idx.reindex(raw_df["DayOfYear"].values).values
    residual_std = float(np.nanstd(raw_df["Price"].values - fitted))

    last2        = sorted(years)[-2:]
    hist         = raw_df[raw_df["Year"].isin(last2)]

    fig = make_subplots(rows=2, cols=1,
        subplot_titles=("Historical + Feb 2022 Forecast", "Feb 2022 — Daily Forecast"),
        vertical_spacing=0.01)

    for yr in last2:
        sub = hist[hist["Year"] == yr].sort_values("Date")
        fig.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Price"], mode="lines", name=str(yr),
            line=dict(color=YEAR_COLORS.get(yr, "#888"), width=1), opacity=0.7,
            hovertemplate="%{x|%b %d %Y}<br>$%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        ), row=1, col=1)

    lo_b = preds - residual_std
    hi_b = preds + residual_std
    fig.add_trace(go.Scatter(
        x=list(feb_dates) + list(feb_dates[::-1]),
        y=list(hi_b) + list(lo_b[::-1]),
        fill="toself", fillcolor="rgba(239,159,39,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name=f"±${residual_std:.1f} band", hoverinfo="skip",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=feb_dates, y=preds, mode="lines+markers", name="Forecast",
        line=dict(color="#EF9F27", width=2.5), marker=dict(size=5),
        hovertemplate="%{x|%b %d}<br>Forecast:&nbsp;&nbsp;$%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=[d.strftime("Feb %d") for d in feb_dates], y=preds,
        marker=dict(color=preds, colorscale="YlOrRd", showscale=False),
        hovertemplate="%{x}<br>$%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        name="Daily forecast", showlegend=False,
    ), row=2, col=1)

    fig.update_layout(
        yaxis =dict(domain=[0.52, 0.90]),
        yaxis2=dict(domain=[0.00, 0.36]),
    )

    anns = list(fig.layout.annotations)
    if len(anns) >= 2:
        anns[0].update(y=0.91, yanchor="bottom")
        anns[1].update(y=0.37, yanchor="bottom")
        fig.update_layout(annotations=anns)

    _layout = {
        **PLOTLY_LAYOUT,
        "title": dict(text=f"Feb 2022 Forecast  (trend slope: {slope:+.2f} USD/yr)"),
        "margin": dict(t=80, b=50, l=60, r=40),
        "hovermode": "x unified",
    }
    fig.update_layout(**_layout)

    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)", showline=True,
                     linecolor="rgba(255,255,255,0.25)", linewidth=1, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", showline=True,
                     linecolor="rgba(255,255,255,0.25)", linewidth=1, zeroline=False,
                     tickprefix="$")
    return fig
