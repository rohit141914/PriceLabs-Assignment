"""
part3_forecast.py
──────────────────
Exercise Part 3 (Bonus) — Estimate Hotel Prices for February 2022

Two strategies are run:
  Strategy A (Simple, no extra deps):
      1. Fit a linear trend on annual medians  →  extrapolate to 2022
      2. Compute a day-of-year seasonal index from historical data
      3. Predicted price = extrapolated_base × seasonal_index

  Strategy B (Prophet, recommended):
      Uses Facebook Prophet for trend + weekly + yearly seasonality.
      Gives a 95% confidence interval per day.
      Install:  pip install prophet

Output files:
  forecast_context.png    – historical prices + Feb 2022 forecast ribbon
  forecast_feb2022.png    – Feb 2022 bar chart (Simple vs Prophet)
  feb2022_forecast.csv    – daily forecast table

Usage:
    python part3_forecast.py                  # default: hotel_prices.csv
    python part3_forecast.py mydata.csv
"""

import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from data_loader import load

warnings.filterwarnings("ignore")

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "hotel_prices.csv"

# ── Load ──────────────────────────────────────────────────────────────────────
df = load(CSV_PATH)

# ── Strategy A: Linear trend + seasonal index ─────────────────────────────────
print("=" * 60)
print("STRATEGY A — Linear Trend + Seasonal Index")
print("=" * 60)

annual = df.groupby("Year")["Price"].median().reset_index()
slope, intercept, r, p, se = stats.linregress(annual["Year"], annual["Price"])
base_2022 = intercept + slope * 2022

print(f"  Slope           : {slope:+.4f} USD / year")
print(f"  Intercept       : {intercept:.2f}")
print(f"  R²              : {r**2:.4f}")
print(f"  Extrapolated base (2022 median) : ${base_2022:.2f}\n")

# Seasonal index per day-of-year
overall_mean  = df["Price"].mean()
seasonal_idx  = df.groupby("DayOfYear")["Price"].mean() / overall_mean

feb_dates     = pd.date_range("2022-02-01", "2022-02-28")
feb_doy       = feb_dates.dayofyear

simple_preds  = (base_2022 * seasonal_idx.reindex(feb_doy).values).round(2)
forecast_df   = pd.DataFrame({"Date": feb_dates, "Simple_Forecast": simple_preds})

print("  Feb 2022 — Simple Forecast:")
print(forecast_df.to_string(index=False), "\n")


# ── Strategy B: Prophet ───────────────────────────────────────────────────────
prophet_available = False
try:
    from prophet import Prophet

    print("=" * 60)
    print("STRATEGY B — Facebook Prophet")
    print("=" * 60)

    prophet_df = df[["Date", "Price"]].rename(columns={"Date": "ds", "Price": "y"})
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
    )
    m.fit(prophet_df)

    # Build future dataframe through Feb 2022
    future = m.make_future_dataframe(periods=int((pd.Timestamp("2022-03-01") -
                                                   df["Date"].max()).days) + 10)
    full_fc = m.predict(future)
    feb_fc  = full_fc[
        (full_fc["ds"] >= "2022-02-01") &
        (full_fc["ds"] <= "2022-02-28")
    ][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    feb_fc.columns = ["Date", "Prophet_Forecast", "Lower_95", "Upper_95"]
    feb_fc = feb_fc.round(2)

    print("  Feb 2022 — Prophet Forecast:")
    print(feb_fc.to_string(index=False), "\n")

    forecast_df = forecast_df.merge(feb_fc, on="Date", how="left")
    prophet_available = True

except ImportError:
    print("ℹ️   Prophet not installed — only Strategy A output produced.")
    print("    Install:  pip install prophet\n")


# ── Save CSV ──────────────────────────────────────────────────────────────────
forecast_df.to_csv("feb2022_forecast.csv", index=False)
print("💾  Saved → feb2022_forecast.csv\n")


# ── Chart 1: Historical context + forecast ───────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 5))

hist = df[df["Date"] >= "2015-01-01"]
ax.plot(hist["Date"], hist["Price"], color="#90caf9",
        linewidth=0.9, alpha=0.8, label="Historical (2015–2016)")

ax.plot(forecast_df["Date"], forecast_df["Simple_Forecast"],
        color="#ffa726", linestyle="--", linewidth=2,
        label="Simple Forecast  (trend + seasonal)")

if prophet_available:
    ax.plot(forecast_df["Date"], forecast_df["Prophet_Forecast"],
            color="#66bb6a", linewidth=2, label="Prophet Forecast")
    ax.fill_between(forecast_df["Date"],
                    forecast_df["Lower_95"], forecast_df["Upper_95"],
                    alpha=0.2, color="#66bb6a", label="95% CI (Prophet)")

ax.axvline(pd.Timestamp("2022-02-01"), color="grey",
           linestyle=":", linewidth=1.2, label="Forecast period")
ax.set_title("Hotel Price Forecast — February 2022  (historical context)")
ax.set_xlabel("Date"); ax.set_ylabel("Price (USD)")
ax.legend(loc="upper left", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("forecast_context.png", dpi=150, bbox_inches="tight")
print("📊  Saved → forecast_context.png")
plt.show()


# ── Chart 2: Feb 2022 bar chart ───────────────────────────────────────────────
day_labels = [str(d) for d in range(1, 29)]
x = np.arange(28)
width = 0.4 if prophet_available else 0.6

fig, ax = plt.subplots(figsize=(15, 4))
bars_a = ax.bar(x - (width/2 if prophet_available else 0),
                forecast_df["Simple_Forecast"],
                width=width, color="#ffa726", label="Simple Forecast", alpha=0.85)

if prophet_available:
    bars_b = ax.bar(x + width/2, forecast_df["Prophet_Forecast"],
                    width=width, color="#66bb6a", label="Prophet Forecast", alpha=0.85)
    ax.errorbar(x + width/2,
                forecast_df["Prophet_Forecast"],
                yerr=[forecast_df["Prophet_Forecast"] - forecast_df["Lower_95"],
                      forecast_df["Upper_95"]  - forecast_df["Prophet_Forecast"]],
                fmt="none", color="grey", capsize=2, linewidth=0.8)

ax.set_xticks(x)
ax.set_xticklabels(day_labels, fontsize=8)
ax.set_title("February 2022 — Daily Hotel Price Forecast")
ax.set_xlabel("Day of February 2022")
ax.set_ylabel("Forecasted Price (USD)")
ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("forecast_feb2022.png", dpi=150, bbox_inches="tight")
print("📊  Saved → forecast_feb2022.png")
plt.show()

print("\n✅  Part 3 complete — 2 charts + feb2022_forecast.csv saved.")
