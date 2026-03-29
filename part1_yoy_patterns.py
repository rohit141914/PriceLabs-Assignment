"""
part1_yoy_patterns.py
──────────────────────
Exercise Part 1 — Year-over-Year Pattern Visualization

Charts produced:
  • yoy_overlay.png      – all years overlaid on a single day-of-year axis
  • yoy_monthly_box.png  – monthly box-plots per year
  • yoy_heatmap.png      – avg-price heatmap (Month × Year)
  • yoy_dow.png          – avg price by day-of-week per year

Usage:
    python part1_yoy_patterns.py                  # default: hotel_prices.csv
    python part1_yoy_patterns.py mydata.csv
"""

import sys
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from data_loader import load

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "hotel_prices.csv"

COLORS = {
    2012: "#4E79A7",
    2013: "#F28E2B",
    2014: "#E15759",
    2015: "#76B7B2",
    2016: "#59A14F",
}

# ── Load ──────────────────────────────────────────────────────────────────────
df = load(CSV_PATH)
years = sorted(df["Year"].unique())


# ── Chart 1: Daily price overlaid by year ────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
for yr in years:
    sub = df[df["Year"] == yr]
    ax.plot(sub["DayOfYear"], sub["Price"],
            color=COLORS.get(yr, "grey"), label=str(yr),
            linewidth=1.2, alpha=0.85)
ax.set_title("Daily Hotel Price Overlaid by Year  (x = day of year 1–365)")
ax.set_xlabel("Day of Year")
ax.set_ylabel("Price (USD)")
ax.legend(title="Year", loc="upper right")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("yoy_overlay.png", dpi=150, bbox_inches="tight")
print("📊  Saved → yoy_overlay.png")
plt.show()


# ── Chart 2: Monthly box-plot per year ───────────────────────────────────────
df["Month_str"] = df["Month"].apply(lambda m: f"{m:02d}")
df["Year_str"]  = df["Year"].astype(str)

fig, ax = plt.subplots(figsize=(16, 5))
sns.boxplot(data=df, x="Month_str", y="Price", hue="Year_str",
            palette=list(COLORS.values()), ax=ax,
            linewidth=0.8, fliersize=2)
ax.set_title("Monthly Price Distribution by Year")
ax.set_xlabel("Month (01 = Jan … 12 = Dec)")
ax.set_ylabel("Price (USD)")
ax.legend(title="Year", loc="upper right", fontsize=8)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("yoy_monthly_box.png", dpi=150, bbox_inches="tight")
print("📊  Saved → yoy_monthly_box.png")
plt.show()


# ── Chart 3: Heatmap — avg price by Month × Year ─────────────────────────────
pivot = df.pivot_table(values="Price", index="Month", columns="Year", aggfunc="mean")
month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"][:len(pivot)]
pivot.index = month_labels

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd",
            linewidths=0.4, ax=ax, cbar_kws={"label": "Avg Price (USD)"})
ax.set_title("Average Price Heatmap  (Month × Year)")
ax.set_xlabel("Year")
ax.set_ylabel("")
plt.tight_layout()
plt.savefig("yoy_heatmap.png", dpi=150, bbox_inches="tight")
print("📊  Saved → yoy_heatmap.png")
plt.show()


# ── Chart 4: Avg price by day-of-week ────────────────────────────────────────
dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
dow_avg    = df.groupby(["Year", "DayOfWeek"])["Price"].mean().reset_index()

fig, ax = plt.subplots(figsize=(8, 4))
for yr in years:
    sub = dow_avg[dow_avg["Year"] == yr]
    ax.plot(sub["DayOfWeek"], sub["Price"],
            marker="o", color=COLORS.get(yr, "grey"),
            label=str(yr), linewidth=1.5)
ax.set_xticks(range(7))
ax.set_xticklabels(dow_labels)
ax.set_title("Average Price by Day of Week")
ax.set_xlabel("Day of Week")
ax.set_ylabel("Avg Price (USD)")
ax.legend(title="Year", fontsize=8)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("yoy_dow.png", dpi=150, bbox_inches="tight")
print("📊  Saved → yoy_dow.png")
plt.show()

print("\n✅  Part 1 complete — 4 charts saved.")
