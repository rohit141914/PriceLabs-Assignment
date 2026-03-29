"""
part2_outliers.py
──────────────────
Part 2 — Outlier Detection & Chart Builders

Functions:
    add_outlier_flags(df)                        – flags outliers using 3 methods
    build_outlier_timeline(full_df, years)        – time-series with outliers highlighted
    build_zscore(full_df, years)                  – z-score over time
    build_histogram(full_df, years, lo, hi)       – price distribution with IQR fences
    build_boxplot(full_df, years)                 – box-plots by year

Detection methods:
    Method A — Global Z-score        (threshold |z| > 2.5)
    Method B — IQR fences            (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
    Method C — Year-relative Z-score (catches within-year anomalies)
    Confirmed outlier when ≥ 2 of 3 methods agree.
"""

from typing import List, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from config import YEAR_COLORS, PLOTLY_LAYOUT, Z_THRESHOLD, IQR_MULT, filter_df


def add_outlier_flags(df: pd.DataFrame) -> Tuple[pd.DataFrame, float, float]:
    df = df.copy()
    df["z_score"]    = np.abs(stats.zscore(df["Price"]))
    df["outlier_z"]  = df["z_score"] > Z_THRESHOLD
    Q1, Q3           = df["Price"].quantile([0.25, 0.75])
    IQR              = Q3 - Q1
    lo, hi           = Q1 - IQR_MULT * IQR, Q3 + IQR_MULT * IQR
    df["outlier_iq"] = (df["Price"] < lo) | (df["Price"] > hi)
    df["z_yr"]       = df.groupby("Year")["Price"].transform(
                           lambda x: np.abs(stats.zscore(x)))
    df["outlier_yr"] = df["z_yr"] > Z_THRESHOLD
    df["outlier"]    = (df[["outlier_z", "outlier_iq", "outlier_yr"]].sum(axis=1) >= 2)
    return df, lo, hi


def build_outlier_timeline(full_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df      = filter_df(full_df, years)
    normal  = df[~df["outlier"]]
    outlier = df[df["outlier"]]
    fig     = go.Figure()
    fig.add_trace(go.Scatter(
        x=normal["Date"], y=normal["Price"], mode="lines", name="Normal",
        line=dict(color="#4E79A7", width=1), opacity=0.7,
        hovertemplate="%{x|%b %d %Y}<br>$%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra>Normal</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=outlier["Date"], y=outlier["Price"], mode="markers",
        name=f"Outlier ({len(outlier)})",
        marker=dict(color="#E15759", size=8, line=dict(color="white", width=1)),
        hovertemplate="%{x|%b %d %Y}<br>$%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra>OUTLIER</extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Price Over Time — Outliers Highlighted",
        xaxis_title="Date", yaxis_title="Price (USD)", hovermode="closest")
    return fig


def build_zscore(full_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df      = filter_df(full_df, years)
    outlier = df[df["outlier"]]
    fig     = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["z_score"].round(3), mode="lines", name="|Z-score|",
        line=dict(color="#76B7B2", width=1),
        hovertemplate="%{x|%b %d %Y}<br>|Z| =&nbsp;&nbsp;%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
    ))
    fig.add_hline(y=Z_THRESHOLD,
        line=dict(color="#E15759", dash="dash", width=1.5),
        annotation_text=f"  threshold ({Z_THRESHOLD})",
        annotation_font_color="#E15759")
    fig.add_trace(go.Scatter(
        x=outlier["Date"], y=outlier["z_score"].round(3), mode="markers",
        name="Outlier", marker=dict(color="#E15759", size=8),
        hovertemplate="%{x|%b %d %Y}<br>|Z| =&nbsp;&nbsp;%{y}&nbsp;&nbsp;&nbsp;&nbsp;<extra>OUTLIER</extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Z-score Over Time", xaxis_title="Date", yaxis_title="|Z-score|")
    return fig


def build_histogram(full_df: pd.DataFrame, years: List[int],
                    lo: float, hi: float) -> go.Figure:
    df      = filter_df(full_df, years)
    normal  = df[~df["outlier"]]
    outlier = df[df["outlier"]]
    fig     = go.Figure()
    fig.add_trace(go.Histogram(
        x=normal["Price"], nbinsx=40, name="Normal",
        marker_color="#4E79A7", opacity=0.8))
    fig.add_trace(go.Histogram(
        x=outlier["Price"], nbinsx=15, name="Outlier",
        marker_color="#E15759", opacity=0.9))
    fig.add_vline(x=lo, line=dict(color="#F28E2B", dash="dash", width=1.5),
        annotation_text=f"  Lower ({lo:.1f})", annotation_font_color="#F28E2B")
    fig.add_vline(x=hi, line=dict(color="#F28E2B", dash="dash", width=1.5),
        annotation_text=f"  Upper ({hi:.1f})", annotation_font_color="#F28E2B")
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Price Distribution with IQR Fences",
        xaxis_title="Price (USD)", yaxis_title="Count", barmode="overlay")
    return fig


def build_boxplot(full_df: pd.DataFrame, years: List[int]) -> go.Figure:
    df  = filter_df(full_df, years)
    fig = go.Figure()
    for yr in years:
        sub = df[df["Year"] == yr]
        fig.add_trace(go.Box(
            y=sub["Price"], name=str(yr),
            marker_color=YEAR_COLORS.get(yr, "#888"), boxmean=True,
            hovertemplate=f"<b>{yr}</b><br>$%{{y}}&nbsp;&nbsp;&nbsp;&nbsp;<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Price Box-Plots by Year",
        xaxis_title="Year", yaxis_title="Price (USD)")
    return fig
