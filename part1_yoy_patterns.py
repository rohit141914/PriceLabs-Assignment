"""
part1_yoy_patterns.py
──────────────────────
Part 1 — Year-over-Year Pattern Chart Builders

Functions:
    build_yoy_overlay(raw_df, years)  – daily prices overlaid by year
    build_monthly_avg(raw_df, years)  – average price per month grouped by year
    build_heatmap(raw_df, years)      – avg-price heatmap (Month × Year)
    build_dow(raw_df, years)          – avg price by day-of-week per year
"""

from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import YEAR_COLORS, PLOTLY_LAYOUT, filter_df


def build_yoy_overlay(raw_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df  = filter_df(raw_df, years)
    fig = go.Figure()
    for yr in years:
        sub = df[df["Year"] == yr].sort_values("DayOfYear")
        fig.add_trace(go.Scatter(
            x=sub["DayOfYear"], y=sub["Price"],
            mode="lines", name=str(yr),
            line=dict(color=YEAR_COLORS.get(yr, "#888"), width=1.6),
            opacity=0.85,
            hovertemplate=f"<b>{yr}</b>&nbsp;&nbsp;&nbsp;Day %{{x}}<br>Price:&nbsp;&nbsp;$%{{y}}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Daily Price Overlaid by Year",
        xaxis_title="Day of Year", yaxis_title="Price (USD)",
        hovermode="x unified")
    return fig


def build_monthly_avg(raw_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df     = filter_df(raw_df, years)
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fig    = go.Figure()
    for yr in years:
        sub  = df[df["Year"] == yr]
        avgs = [sub[sub["Month"] == m+1]["Price"].mean() for m in range(12)]
        fig.add_trace(go.Bar(
            x=months, y=[round(v, 1) if not np.isnan(v) else 0 for v in avgs],
            name=str(yr), marker_color=YEAR_COLORS.get(yr, "#888"), opacity=0.85,
            hovertemplate=f"<b>{yr}</b>&nbsp;&nbsp;&nbsp;%{{x}}<br>Avg:&nbsp;&nbsp;&nbsp;$%{{y}}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Average Monthly Price by Year",
        xaxis_title="Month", yaxis_title="Avg Price (USD)", barmode="group")
    return fig


def build_heatmap(raw_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df     = filter_df(raw_df, years)
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    z      = []
    for m in range(1, 13):
        row = [round(float(df[(df["Year"]==yr) & (df["Month"]==m)]["Price"].mean()), 1)
               if len(df[(df["Year"]==yr) & (df["Month"]==m)]) else None
               for yr in years]
        z.append(row)
    fig = go.Figure(go.Heatmap(
        z=z, x=[str(y) for y in years], y=months,
        colorscale="YlOrRd",
        text=[[f"${v}" if v else "" for v in row] for row in z],
        texttemplate="%{text}",
        hovertemplate="Year: %{x}&nbsp;&nbsp;&nbsp;Month: %{y}<br>Avg:&nbsp;&nbsp;&nbsp;$%{z}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        colorbar=dict(title="USD", tickfont=dict(color="#e2e8f0")),
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Avg Price Heatmap  (Month × Year)", xaxis_title="Year")
    return fig


def build_dow(raw_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df         = filter_df(raw_df, years)
    dow_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    fig        = go.Figure()
    for yr in years:
        sub = df[df["Year"]==yr].groupby("DayOfWeek")["Price"].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=[dow_labels[d] for d in sub["DayOfWeek"]],
            y=sub["Price"].round(1),
            mode="lines+markers", name=str(yr),
            line=dict(color=YEAR_COLORS.get(yr, "#888"), width=2),
            marker=dict(size=7),
            hovertemplate=f"<b>{yr}</b>&nbsp;&nbsp;&nbsp;%{{x}}<br>Avg:&nbsp;&nbsp;&nbsp;$%{{y}}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Avg Price by Day of Week",
        xaxis_title="Day of Week", yaxis_title="Avg Price (USD)")
    return fig
