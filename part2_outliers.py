"""
part2_outliers.py
──────────────────
Exercise Part 2 — Outlier Detection (Visual + Programmatic)

Three methods are applied and results are combined:
  Method A — Global Z-score          (threshold |z| > 2.5)
  Method B — IQR fences              (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
  Method C — Year-relative Z-score   (catches within-year anomalies)

A point is flagged as a confirmed outlier when ≥ 2 of 3 methods agree.

Output files:
  outliers_timeline.png   – full time-series with red outlier dots
  outliers_boxplot.png    – box-plots per year (fliers are outliers)
  outliers_zscore.png     – z-score over time with threshold line
  outliers_histogram.png  – price distribution with IQR fences
  outliers.csv            – all detected outlier rows

Usage:
    python part2_outliers.py                  # default: hotel_prices.csv
    python part2_outliers.py mydata.csv
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from data_loader import load

CSV_PATH     = sys.argv[1] if len(sys.argv) > 1 else "hotel_prices.csv"
Z_THRESHOLD  = 2.5
IQR_MULT     = 1.5
COLORS       = {2012:"#4E79A7",2013:"#F28E2B",2014:"#E15759",2015:"#76B7B2",2016:"#59A14F"}


# ── Load ──────────────────────────────────────────────────────────────────────
df = load(CSV_PATH)


# ── Programmatic detection ────────────────────────────────────────────────────

# Method A — global z-score
df["z_score"]   = np.abs(stats.zscore(df["Price"]))
df["outlier_z"] = df["z_score"] > Z_THRESHOLD

# Method B — IQR
Q1, Q3          = df["Price"].quantile([0.25, 0.75])
IQR             = Q3 - Q1
lo_fence        = Q1 - IQR_MULT * IQR
hi_fence        = Q3 + IQR_MULT * IQR
df["outlier_iq"]= (df["Price"] < lo_fence) | (df["Price"] > hi_fence)

# Method C — year-relative z-score
df["z_yr"]      = df.groupby("Year")["Price"].transform(
                      lambda x: np.abs(stats.zscore(x))
                  )
df["outlier_yr"]= df["z_yr"] > Z_THRESHOLD

# Combined flag
df["outlier"]   = (df[["outlier_z","outlier_iq","outlier_yr"]].sum(axis=1) >= 2)

# ── Print report ──────────────────────────────────────────────────────────────
n_out = df["outlier"].sum()
print("=" * 60)
print("OUTLIER DETECTION REPORT")
print("=" * 60)
print(f"  Method A  Global Z-score  (|z|>{Z_THRESHOLD})    : {df['outlier_z'].sum()} rows")
print(f"  Method B  IQR fences  (×{IQR_MULT})              : {df['outlier_iq'].sum()} rows")
print(f"            Lower fence : {lo_fence:.2f}")
print(f"            Upper fence : {hi_fence:.2f}")
print(f"  Method C  Year-relative Z-score        : {df['outlier_yr'].sum()} rows")
print(f"  ➜  Confirmed (≥2 methods)              : {n_out} rows")
print()
if n_out > 0:
    cols = ["Date","Price","z_score","outlier_z","outlier_iq","outlier_yr"]
    print(df[df["outlier"]][cols].to_string(index=False))
    df[df["outlier"]][cols].to_csv("outliers.csv", index=False)
    print("\n💾  Saved → outliers.csv")
else:
    print("  No confirmed outliers found.")
print()

normal  = df[~df["outlier"]]
outlier = df[df["outlier"]]


# ── Chart 1: Time-series with outlier highlights ──────────────────────────────
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(df["Date"], df["Price"], color="#90caf9", linewidth=0.8, alpha=0.7, label="Normal")
ax.scatter(outlier["Date"], outlier["Price"],
           color="#e53935", zorder=5, s=45, label=f"Outlier ({n_out})")
ax.set_title("Hotel Price Over Time — Confirmed Outliers Highlighted")
ax.set_xlabel("Date"); ax.set_ylabel("Price (USD)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("outliers_timeline.png", dpi=150, bbox_inches="tight")
print("📊  Saved → outliers_timeline.png")
plt.show()


# ── Chart 2: Box-plots per year ───────────────────────────────────────────────
years = sorted(df["Year"].unique())
fig, ax = plt.subplots(figsize=(9, 5))
data_by_year = [df[df["Year"] == y]["Price"].values for y in years]
bp = ax.boxplot(data_by_year, labels=years, patch_artist=True,
                flierprops=dict(marker="o", markerfacecolor="#e53935",
                                markersize=5, linestyle="none"))
for patch, yr in zip(bp["boxes"], years):
    patch.set_facecolor(COLORS.get(yr, "#ccc"))
ax.set_title("Price Box-Plots by Year  (red dots = outliers)")
ax.set_xlabel("Year"); ax.set_ylabel("Price (USD)")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("outliers_boxplot.png", dpi=150, bbox_inches="tight")
print("📊  Saved → outliers_boxplot.png")
plt.show()


# ── Chart 3: Z-score timeline ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 3.5))
ax.plot(df["Date"], df["z_score"], color="#78909c", linewidth=0.7, alpha=0.8)
ax.axhline(Z_THRESHOLD, color="#e53935", linestyle="--", linewidth=1.2,
           label=f"Threshold ({Z_THRESHOLD})")
ax.scatter(outlier["Date"], outlier["z_score"], color="#e53935", s=40, zorder=5)
ax.set_title("Global Z-score Over Time")
ax.set_xlabel("Date"); ax.set_ylabel("|Z-score|")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("outliers_zscore.png", dpi=150, bbox_inches="tight")
print("📊  Saved → outliers_zscore.png")
plt.show()


# ── Chart 4: Price histogram with IQR fences ─────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4))
ax.hist(normal["Price"],  bins=40, color="#90caf9", alpha=0.8, label="Normal")
ax.hist(outlier["Price"], bins=10, color="#e53935", alpha=0.9, label=f"Outlier ({n_out})")
ax.axvline(lo_fence, color="#ff7043", linestyle="--", linewidth=1.3,
           label=f"IQR lower fence  ({lo_fence:.1f})")
ax.axvline(hi_fence, color="#ff7043", linestyle="--", linewidth=1.3,
           label=f"IQR upper fence  ({hi_fence:.1f})")
ax.set_title("Price Distribution with IQR Fences")
ax.set_xlabel("Price (USD)"); ax.set_ylabel("Count")
ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("outliers_histogram.png", dpi=150, bbox_inches="tight")
print("📊  Saved → outliers_histogram.png")
plt.show()

print("\n✅  Part 2 complete — 4 charts + outliers.csv saved.")
