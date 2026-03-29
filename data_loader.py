"""
data_loader.py
──────────────
Loads and cleans the hotel prices CSV.
"""

import pandas as pd


def load(path: str = "hotel_prices.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    df.columns = df.columns.str.strip()
    df = df.sort_values("Date").reset_index(drop=True)
    df["Year"]      = df["Date"].dt.year
    df["Month"]     = df["Date"].dt.month
    df["DayOfYear"] = df["Date"].dt.dayofyear
    df["DayOfWeek"] = df["Date"].dt.dayofweek
    df["MonthName"] = df["Date"].dt.strftime("%b")
    return df
