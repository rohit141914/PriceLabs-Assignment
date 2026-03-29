"""
run_all.py
───────────
Convenience runner — executes all three parts in sequence.

Usage:
    python run_all.py                   # default: hotel_prices.csv
    python run_all.py my_data.csv
"""

import sys
import subprocess

csv = sys.argv[1] if len(sys.argv) > 1 else "hotel_prices.csv"
scripts = [
    "part1_yoy_patterns.py",
    "part2_outliers.py",
    "part3_forecast.py",
]

for s in scripts:
    print(f"\n{'='*60}")
    print(f"  Running  {s}")
    print(f"{'='*60}\n")
    result = subprocess.run([sys.executable, s, csv])
    if result.returncode != 0:
        print(f"❌  {s} failed — stopping.")
        sys.exit(1)

print("\n🎉  All parts complete!")
