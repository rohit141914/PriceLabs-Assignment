"""
app.py  ─  FastAPI Hotel Price Analytics Server
─────────────────────────────────────────────────
Usage:
    uvicorn app:app --reload --port 5000
Then open:  http://localhost:5000
"""

import sys
import json
import warnings
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
_first_arg  = sys.argv[1] if len(sys.argv) > 1 else ""
CSV_PATH    = _first_arg if _first_arg.endswith(".csv") else "hotel_prices.csv"
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
    font=dict(family="DM Sans, sans-serif", color="#e2e8f0", size=12),
    margin=dict(l=50, r=30, t=40, b=50),
    legend=dict(
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", showline=False, zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", showline=False, zeroline=False),
)

# ─── FastAPI app + templates ──────────────────────────────────────────────────
app       = FastAPI(title="Hotel Price Analytics", version="1.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


# ─── Data loading ─────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
    df.columns = df.columns.str.strip()
    df = df.sort_values("Date").reset_index(drop=True)
    df["Year"]      = df["Date"].dt.year
    df["Month"]     = df["Date"].dt.month
    df["DayOfYear"] = df["Date"].dt.dayofyear
    df["DayOfWeek"] = df["Date"].dt.dayofweek
    df["MonthName"] = df["Date"].dt.strftime("%b")
    return df


def add_outlier_flags(df: pd.DataFrame):
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


RAW_DF             = load_data()
FULL_DF, LO, HI    = add_outlier_flags(RAW_DF)
ALL_YEARS: list    = sorted(RAW_DF["Year"].unique().tolist())


# ─── Helpers ──────────────────────────────────────────────────────────────────
def fig_json(fig) -> dict:
    return json.loads(fig.to_json())


def filter_df(df: pd.DataFrame, years: List[int]) -> pd.DataFrame:
    return df[df["Year"].isin(years)] if years else df


# ─── Chart builders ───────────────────────────────────────────────────────────

def build_yoy_overlay(years: List[int]) -> go.Figure:
    df  = filter_df(RAW_DF, years)
    fig = go.Figure()
    for yr in years:
        sub = df[df["Year"] == yr].sort_values("DayOfYear")
        fig.add_trace(go.Scatter(
            x=sub["DayOfYear"], y=sub["Price"],
            mode="lines", name=str(yr),
            line=dict(color=YEAR_COLORS.get(yr, "#888"), width=1.6),
            opacity=0.85,
            hovertemplate=f"<b>{yr}</b>  Day %{{x}}<br>Price: $%{{y}}<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Daily Price Overlaid by Year",
        xaxis_title="Day of Year", yaxis_title="Price (USD)",
        hovermode="x unified")
    return fig


def build_monthly_avg(years: List[int]) -> go.Figure:
    df     = filter_df(RAW_DF, years)
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fig    = go.Figure()
    for yr in years:
        sub  = df[df["Year"] == yr]
        avgs = [sub[sub["Month"] == m+1]["Price"].mean() for m in range(12)]
        fig.add_trace(go.Bar(
            x=months, y=[round(v, 1) if not np.isnan(v) else 0 for v in avgs],
            name=str(yr), marker_color=YEAR_COLORS.get(yr, "#888"), opacity=0.85,
            hovertemplate=f"<b>{yr}</b>  %{{x}}<br>Avg: $%{{y}}<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Average Monthly Price by Year",
        xaxis_title="Month", yaxis_title="Avg Price (USD)", barmode="group")
    return fig


def build_heatmap(years: List[int]) -> go.Figure:
    df     = filter_df(RAW_DF, years)
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
        hovertemplate="Year: %{x}  Month: %{y}<br>Avg: $%{z}<extra></extra>",
        colorbar=dict(title="USD", tickfont=dict(color="#e2e8f0")),
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Avg Price Heatmap  (Month × Year)", xaxis_title="Year")
    return fig


def build_dow(years: List[int]) -> go.Figure:
    df         = filter_df(RAW_DF, years)
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
            hovertemplate=f"<b>{yr}</b>  %{{x}}<br>Avg: $%{{y}}<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Avg Price by Day of Week",
        xaxis_title="Day of Week", yaxis_title="Avg Price (USD)")
    return fig


def build_outlier_timeline(years: List[int]) -> go.Figure:
    df      = filter_df(FULL_DF, years)
    normal  = df[~df["outlier"]]
    outlier = df[df["outlier"]]
    fig     = go.Figure()
    fig.add_trace(go.Scatter(
        x=normal["Date"], y=normal["Price"], mode="lines", name="Normal",
        line=dict(color="#4E79A7", width=1), opacity=0.7,
        hovertemplate="%{x|%b %d %Y}<br>$%{y}<extra>Normal</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=outlier["Date"], y=outlier["Price"], mode="markers",
        name=f"Outlier ({len(outlier)})",
        marker=dict(color="#E15759", size=8, line=dict(color="white", width=1)),
        hovertemplate="%{x|%b %d %Y}<br>$%{y}<extra>OUTLIER</extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Price Over Time — Outliers Highlighted",
        xaxis_title="Date", yaxis_title="Price (USD)", hovermode="closest")
    return fig


def build_zscore(years: List[int]) -> go.Figure:
    df      = filter_df(FULL_DF, years)
    outlier = df[df["outlier"]]
    fig     = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["z_score"].round(3), mode="lines", name="|Z-score|",
        line=dict(color="#76B7B2", width=1),
        hovertemplate="%{x|%b %d %Y}<br>|Z| = %{y}<extra></extra>",
    ))
    fig.add_hline(y=Z_THRESHOLD,
        line=dict(color="#E15759", dash="dash", width=1.5),
        annotation_text=f"  threshold ({Z_THRESHOLD})",
        annotation_font_color="#E15759")
    fig.add_trace(go.Scatter(
        x=outlier["Date"], y=outlier["z_score"].round(3), mode="markers",
        name="Outlier", marker=dict(color="#E15759", size=8),
        hovertemplate="%{x|%b %d %Y}<br>|Z| = %{y}<extra>OUTLIER</extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Z-score Over Time", xaxis_title="Date", yaxis_title="|Z-score|")
    return fig


def build_histogram(years: List[int]) -> go.Figure:
    df      = filter_df(FULL_DF, years)
    normal  = df[~df["outlier"]]
    outlier = df[df["outlier"]]
    fig     = go.Figure()
    fig.add_trace(go.Histogram(
        x=normal["Price"], nbinsx=40, name="Normal",
        marker_color="#4E79A7", opacity=0.8))
    fig.add_trace(go.Histogram(
        x=outlier["Price"], nbinsx=15, name="Outlier",
        marker_color="#E15759", opacity=0.9))
    fig.add_vline(x=LO, line=dict(color="#F28E2B", dash="dash", width=1.5),
        annotation_text=f"  Lower ({LO:.1f})", annotation_font_color="#F28E2B")
    fig.add_vline(x=HI, line=dict(color="#F28E2B", dash="dash", width=1.5),
        annotation_text=f"  Upper ({HI:.1f})", annotation_font_color="#F28E2B")
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Price Distribution with IQR Fences",
        xaxis_title="Price (USD)", yaxis_title="Count", barmode="overlay")
    return fig


def build_boxplot(years: List[int]) -> go.Figure:
    df  = filter_df(FULL_DF, years)
    fig = go.Figure()
    for yr in years:
        sub = df[df["Year"] == yr]
        fig.add_trace(go.Box(
            y=sub["Price"], name=str(yr),
            marker_color=YEAR_COLORS.get(yr, "#888"), boxmean=True,
            hovertemplate=f"<b>{yr}</b><br>%{{y}}<extra></extra>",
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Price Box-Plots by Year",
        xaxis_title="Year", yaxis_title="Price (USD)")
    return fig


def build_forecast(years: List[int]) -> go.Figure:
    df     = filter_df(RAW_DF, years)
    annual = df.groupby("Year")["Price"].median().reset_index()
    if len(annual) >= 2:
        slope, intercept, *_ = stats.linregress(annual["Year"], annual["Price"])
    else:
        slope, intercept = 0.0, float(annual["Price"].iloc[0])
    base_2022    = intercept + slope * 2022
    overall_mean = RAW_DF["Price"].mean()
    seasonal_idx = RAW_DF.groupby("DayOfYear")["Price"].mean() / overall_mean
    feb_dates    = pd.date_range("2022-02-01", "2022-02-28")
    preds        = (base_2022 * seasonal_idx.reindex(feb_dates.dayofyear).values).round(2)
    last2        = sorted(years)[-2:]
    hist         = RAW_DF[RAW_DF["Year"].isin(last2)]

    fig = make_subplots(rows=2, cols=1, row_heights=[0.55, 0.45],
        subplot_titles=("Historical + Feb 2022 Forecast", "Feb 2022 — Daily Forecast"),
        vertical_spacing=0.14)

    for yr in last2:
        sub = hist[hist["Year"] == yr].sort_values("Date")
        fig.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Price"], mode="lines", name=str(yr),
            line=dict(color=YEAR_COLORS.get(yr, "#888"), width=1), opacity=0.7,
            hovertemplate="%{x|%b %d %Y}<br>$%{y}<extra></extra>",
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
        hovertemplate="%{x|%b %d}<br>Forecast: $%{y}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=[d.strftime("Feb %d") for d in feb_dates], y=preds,
        marker=dict(color=preds, colorscale="YlOrRd", showscale=False),
        hovertemplate="%{x}<br>$%{y}<extra></extra>",
        name="Daily forecast", showlegend=False,
    ), row=2, col=1)

    fig.update_layout(**PLOTLY_LAYOUT,
        title=f"Feb 2022 Forecast  (trend slope: {slope:+.2f} USD/yr)",
        hovermode="x unified")
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)", showline=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)", showline=False, zeroline=False,
                     tickprefix="$")
    return fig


CHART_MAP = {
    "yoy_overlay":      build_yoy_overlay,
    "monthly_avg":      build_monthly_avg,
    "heatmap":          build_heatmap,
    "dow":              build_dow,
    "outlier_timeline": build_outlier_timeline,
    "zscore":           build_zscore,
    "histogram":        build_histogram,
    "boxplot":          build_boxplot,
    "forecast":         build_forecast,
}


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"years": ALL_YEARS}
    )


@app.get("/api/stats")
async def api_stats(years: str = Query(default="")):
    """Summary stats for the metric cards."""
    yr_list = [int(y) for y in years.split(",") if y] if years else ALL_YEARS
    df  = filter_df(RAW_DF,  yr_list)
    out = filter_df(FULL_DF, yr_list)
    return {
        "total_days":     int(len(df)),
        "avg_price":      round(float(df["Price"].mean()), 1),
        "min_price":      int(df["Price"].min()),
        "max_price":      int(df["Price"].max()),
        "outlier_count":  int(out["outlier"].sum()),
    }


@app.get("/api/outliers")
async def api_outliers(years: str = Query(default="")):
    """Return confirmed outlier rows for the sidebar table."""
    yr_list = [int(y) for y in years.split(",") if y] if years else ALL_YEARS
    df = filter_df(FULL_DF, yr_list)
    df = df[df["outlier"]]
    return [
        {
            "date":    r["Date"].strftime("%b %d, %Y"),
            "price":   int(r["Price"]),
            "zscore":  round(float(r["z_score"]), 3),
            "flag_z":  bool(r["outlier_z"]),
            "flag_iq": bool(r["outlier_iq"]),
            "flag_yr": bool(r["outlier_yr"]),
        }
        for _, r in df.iterrows()
    ]


@app.get("/api/chart/{chart_id}")
async def api_chart(chart_id: str, years: str = Query(default="")):
    """Return a Plotly figure as JSON."""
    if chart_id not in CHART_MAP:
        return JSONResponse({"error": f"Unknown chart: {chart_id}"}, status_code=404)
    yr_list = [int(y) for y in years.split(",") if y] if years else ALL_YEARS
    fig     = CHART_MAP[chart_id](yr_list)
    return JSONResponse(fig_json(fig))


app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# ─── Dev runner ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print(f"✅  Loaded '{CSV_PATH}'  ({len(RAW_DF):,} rows)  |  years: {ALL_YEARS}")
    print("🚀  Starting server → http://localhost:5000\n")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
