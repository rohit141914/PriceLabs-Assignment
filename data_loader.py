"""
data_loader.py
──────────────
Loads and cleans the hotel prices CSV.
Used by all other scripts.
"""

import pandas as pd
import sys


def load(path: str = "hotel_prices.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    df.columns = df.columns.str.strip()
    df = df.sort_values("Date").reset_index(drop=True)

    df["Year"]       = df["Date"].dt.year
    df["Month"]      = df["Date"].dt.month
    df["DayOfYear"]  = df["Date"].dt.dayofyear
    df["DayOfWeek"]  = df["Date"].dt.dayofweek   # 0=Mon … 6=Sun
    df["WeekOfYear"] = df["Date"].dt.isocalendar().week.astype(int)
    df["MonthName"]  = df["Date"].dt.strftime("%b")

    print(f"✅  Loaded {len(df):,} rows  |  years: {df['Year'].min()}–{df['Year'].max()}")
    print(df[["Date", "Price"]].describe(), "\n")
    return df


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "hotel_prices.csv"
    df = load(path)
    print(df.head(10).to_string(index=False))
