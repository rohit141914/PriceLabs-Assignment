# Hotel Price Analytics

An interactive web application for analysing hotel price data (2012–2016). Built with FastAPI and Plotly, it covers year-over-year pattern analysis, multi-method outlier detection, and a February 2022 price forecast.

---

## Features

### Part 1 — Year-over-Year Patterns
Four interactive charts for spotting seasonal and weekly pricing cycles:

| Chart | What it shows |
|---|---|
| Day-of-year overlay | All years plotted on a single 1–365 axis for direct comparison |
| Monthly averages | Grouped bar chart of average price per month, split by year |
| Month × Year heatmap | Color-coded grid — cool = cheap, warm = expensive |
| Day-of-week pattern | Mon–Sun average prices per year to reveal weekend vs weekday trends |

### Part 2 — Outlier Detection
Three independent detection methods, confirmed when **≥ 2 of 3 agree**:

| Method | Rule |
|---|---|
| Global Z-score | `\|z\| > 2.5` from the overall dataset mean |
| IQR fences | Outside `Q1 − 1.5×IQR` or `Q3 + 1.5×IQR` |
| Year-relative Z-score | `\|z\| > 2.5` within each individual year |

Four visual charts: timeline with outlier markers, z-score over time, price histogram with IQR fence lines, and per-year box plots. A detail table lists every confirmed outlier with its date, price, z-score, and which methods flagged it.

### Part 3 — February 2022 Forecast (Bonus)
Predicts a price for each of the 28 days in February 2022 using a two-component model:

1. **Linear trend** — fits a regression on annual median prices and extrapolates to 2022
2. **Seasonal index** — computes a day-of-year multiplier (`avg_price[day] / overall_mean`) from the full historical dataset

```
predicted_price = (intercept + slope × 2022) × seasonal_index[day_of_year]
```

The uncertainty band is ±1 standard deviation of the model's in-sample residuals. A daily predictions table is shown alongside the chart.

---

## Project Structure

```
Pricelab/
├── app.py                 # FastAPI server — routes and startup
├── config.py              # Shared constants (thresholds, colors, layout)
├── data_loader.py         # CSV loading and feature extraction
├── part1_yoy_patterns.py  # YoY chart builders
├── part2_outliers.py      # Outlier detection and chart builders
├── part3_forecast.py      # Forecast chart builder and data endpoint
├── hotel_prices.csv       # Daily hotel prices 2012–2016
├── templates/
│   └── index.html         # Frontend HTML (Jinja2)
├── static/
│   ├── app.js             # Chart switching, API calls, year filter
│   └── style.css          # Dark/light theme styles
└── requirements.txt
```

---

## Setup

**1. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run the server**

```bash
uvicorn app:app --reload --port 5000
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Main dashboard (HTML) |
| `GET` | `/api/stats?years=` | Summary metrics (total days, avg/min/max price, outlier count) |
| `GET` | `/api/outliers?years=` | List of confirmed outlier rows |
| `GET` | `/api/chart/{chart_id}?years=` | Plotly figure JSON for any chart |
| `GET` | `/api/forecast?years=` | 28 daily Feb 2022 price predictions |

**Chart IDs:** `yoy_overlay`, `monthly_avg`, `heatmap`, `dow`, `outlier_timeline`, `zscore`, `histogram`, `boxplot`, `forecast`

The `years` parameter accepts a comma-separated list (e.g. `years=2012,2014,2016`). Omit it to include all years.

---

## Data

`hotel_prices.csv` — 1,475 rows of daily hotel prices from 2012 to 2016.

```
Date,Price
1/1/2012,99
1/2/2012,95
...
```

---

## Tech Stack

- **Backend:** Python, FastAPI, Pandas, NumPy, SciPy, Plotly
- **Frontend:** Vanilla JS, Plotly.js, CSS custom properties (dark/light theme)
