
from pathlib import Path
import pandas as pd

input_file = Path(
    "data/fintech/malaysia_payment_systems_2016_2026.csv"
)

output_folder = Path("data/fintech/analysis")
output_folder.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_file)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df["system"] = df["system"].astype(str).str.lower().str.strip()

df = df.dropna(subset=["date", "volume", "value", "system"])

# Compare the same six months in both years.
periods = {
    "Jan-Jun 2025": (2025, 1, 6),
    "Jan-Jun 2026": (2026, 1, 6),
}

results = []

for system in sorted(df["system"].unique()):
    totals = {}

    for label, (year, start_month, end_month) in periods.items():
        selected = df[
            (df["system"] == system)
            & (df["date"].dt.year == year)
            & (df["date"].dt.month.between(start_month, end_month))
        ]

        months_present = selected["date"].dt.to_period("M").nunique()

        totals[label] = {
            "volume": selected["volume"].sum(),
            "value": selected["value"].sum(),
            "months": months_present,
        }

    old = totals["Jan-Jun 2025"]
    new = totals["Jan-Jun 2026"]

    # Only calculate growth if both periods contain all six months.
    valid_comparison = old["months"] == 6 and new["months"] == 6

    volume_growth = (
        (new["volume"] / old["volume"] - 1) * 100
        if valid_comparison and old["volume"] != 0
        else None
    )

    value_growth = (
        (new["value"] / old["value"] - 1) * 100
        if valid_comparison and old["value"] != 0
        else None
    )

    results.append({
        "system": system,
        "months_2025": old["months"],
        "months_2026": new["months"],
        "volume_2025": old["volume"],
        "volume_2026": new["volume"],
        "volume_growth_pct": volume_growth,
        "value_2025": old["value"],
        "value_2026": new["value"],
        "value_growth_pct": value_growth,
        "comparison_valid": valid_comparison,
    })

comparison = pd.DataFrame(results)

comparison.to_csv(
    output_folder / "jan_jun_2025_vs_2026.csv",
    index=False,
    encoding="utf-8-sig",
)

comparison.to_excel(
    output_folder / "jan_jun_2025_vs_2026.xlsx",
    index=False,
)

print("\nJANUARY-JUNE COMPARISON")
print(comparison.to_string(index=False))
print("\nSaved to:", output_folder.resolve())
