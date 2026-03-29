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
    last2        = sorted(years)[-2:]
    hist         = raw_df[raw_df["Year"].isin(last2)]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.55, 0.45],
        subplot_titles=("Historical + Feb 2022 Forecast", "Feb 2022 — Daily Forecast"),
        vertical_spacing=0.14)

    for yr in last2:
        sub = hist[hist["Year"] == yr].sort_values("Date")
        fig.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Price"], mode="lines", name=str(yr),
            line=dict(color=YEAR_COLORS.get(yr, "#888"), width=1), opacity=0.7,
            hovertemplate="%{x|%b %d %Y}<br>$%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        ), row=1, col=1)

    lo_b = preds - 8
    hi_b = preds + 8
    fig.add_trace(go.Scatter(
        x=list(feb_dates) + list(feb_dates[::-1]),
        y=list(hi_b) + list(lo_b[::-1]),
        fill="toself", fillcolor="rgba(239,159,39,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name="±8 USD band", hoverinfo="skip",
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

    fig.update_layout(**PLOTLY_LAYOUT,
        title=f"Feb 2022 Forecast  (trend slope: {slope:+.2f} USD/yr)",
        hovermode="x unified")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)", showline=True,
                     linecolor="rgba(255,255,255,0.25)", linewidth=1, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", showline=True,
                     linecolor="rgba(255,255,255,0.25)", linewidth=1, zeroline=False,
                     tickprefix="$")
    return fig
