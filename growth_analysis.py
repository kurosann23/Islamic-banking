
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

# Aggregate by month and payment system.
monthly = (
    df.groupby(
        [pd.Grouper(key="date", freq="MS"), "system"],
        as_index=False
    )
    .agg(
        volume=("volume", "sum"),
        value=("value", "sum")
    )
    .sort_values(["system", "date"])
)

# Compare each month with the same month one year earlier.
monthly["volume_previous_year"] = (
    monthly.groupby("system")["volume"].shift(12)
)

monthly["value_previous_year"] = (
    monthly.groupby("system")["value"].shift(12)
)

monthly["volume_yoy_pct"] = (
    monthly["volume"] / monthly["volume_previous_year"] - 1
) * 100

monthly["value_yoy_pct"] = (
    monthly["value"] / monthly["value_previous_year"] - 1
) * 100

# Avoid misleading infinite results if a prior value is zero.
monthly = monthly.replace([float("inf"), float("-inf")], pd.NA)

# Save detailed monthly growth results.
monthly.to_csv(
    output_folder / "monthly_yoy_growth.csv",
    index=False,
    encoding="utf-8-sig"
)

# Summarise average growth by payment system and year.
monthly["year"] = monthly["date"].dt.year

yearly_growth = (
    monthly.groupby(["year", "system"], as_index=False)
    .agg(
        average_volume_yoy=("volume_yoy_pct", "mean"),
        average_value_yoy=("value_yoy_pct", "mean"),
        months_with_volume_yoy=("volume_yoy_pct", "count"),
        months_with_value_yoy=("value_yoy_pct", "count")
    )
)

yearly_growth.to_excel(
    output_folder / "yearly_yoy_growth.xlsx",
    index=False
)

print("\nMONTHLY YEAR-ON-YEAR GROWTH")
print(
    monthly[
        [
            "date",
            "system",
            "volume_yoy_pct",
            "value_yoy_pct"
        ]
    ].tail(18).to_string(index=False)
)

print("\nAVERAGE MONTHLY YOY GROWTH BY YEAR")
print(yearly_growth.tail(24).to_string(index=False))

print("\nFiles saved to:", output_folder.resolve())
