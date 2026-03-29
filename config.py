"""
config.py
──────────
Shared constants and helpers used across all chart modules and app.py.
"""

from typing import List
import pandas as pd

Z_THRESHOLD = 2.5
IQR_MULT    = 1.5

YEAR_COLORS = {
    2012: "#4E79A7",
    2013: "#F28E2B",
    2014: "#E15759",
    2015: "#76B7B2",
    2016: "#59A14F",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#e2e8f0", size=14),
    margin=dict(l=50, r=30, t=40, b=50),
    legend=dict(
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", showline=True,
               linecolor="rgba(255,255,255,0.25)", linewidth=1, zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", showline=True,
               linecolor="rgba(255,255,255,0.25)", linewidth=1, zeroline=False),
    hoverlabel=dict(
        bgcolor="#1e2530",
        bordercolor="rgba(255,255,255,0.15)",
        font=dict(family="DM Sans, sans-serif", color="#e2e8f0", size=14),
        namelength=-1,
        align="left",
    ),
)


def filter_df(df: pd.DataFrame, years: List[int]) -> pd.DataFrame:
    return df[df["Year"].isin(years)] if years else df
