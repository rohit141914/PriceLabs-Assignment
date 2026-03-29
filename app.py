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
import pandas as pd

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import filter_df
from part1_yoy_patterns import build_yoy_overlay, build_monthly_avg, build_heatmap, build_dow
from part2_outliers import add_outlier_flags, build_outlier_timeline, build_zscore, build_histogram, build_boxplot
from part3_forecast import build_forecast

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
_first_arg = sys.argv[1] if len(sys.argv) > 1 else ""
CSV_PATH   = _first_arg if _first_arg.endswith(".csv") else "hotel_prices.csv"

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


RAW_DF             = load_data()
FULL_DF, LO, HI    = add_outlier_flags(RAW_DF)
ALL_YEARS: list    = sorted(RAW_DF["Year"].unique().tolist())


# ─── Helpers ──────────────────────────────────────────────────────────────────
def fig_json(fig) -> dict:
    return json.loads(fig.to_json())


CHART_MAP = {
    "yoy_overlay":      lambda years: build_yoy_overlay(RAW_DF, years),
    "monthly_avg":      lambda years: build_monthly_avg(RAW_DF, years),
    "heatmap":          lambda years: build_heatmap(RAW_DF, years),
    "dow":              lambda years: build_dow(RAW_DF, years),
    "outlier_timeline": lambda years: build_outlier_timeline(FULL_DF, years),
    "zscore":           lambda years: build_zscore(FULL_DF, years),
    "histogram":        lambda years: build_histogram(FULL_DF, years, LO, HI),
    "boxplot":          lambda years: build_boxplot(FULL_DF, years),
    "forecast":         lambda years: build_forecast(RAW_DF, years),
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
