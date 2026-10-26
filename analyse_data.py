
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------
# 1. File locations
# --------------------------------

input_file = Path("data/islamic_banking_cleaned.xlsx")
output_folder = Path("data/analysis")

output_folder.mkdir(parents=True, exist_ok=True)

# --------------------------------
# 2. Read the Islamic Banks sheet
# --------------------------------

df = pd.read_excel(
    input_file,
    sheet_name="Islamic_Banks"
)

print("Dataset loaded successfully!")
print("Number of records:", len(df))
print("\nAvailable columns:")
print(df.columns.tolist())

# --------------------------------
# 3. Check required columns
# --------------------------------

required_columns = [
    "year_dt",
    "month_dt",
    "total_assets"
]

for column in required_columns:
    if column not in df.columns:
        raise ValueError(
            f"Missing required column: {column}"
        )

# --------------------------------
# 4. Clean the important fields
# --------------------------------

df["year_dt"] = pd.to_numeric(
    df["year_dt"], errors="coerce"
)

df["month_dt"] = pd.to_numeric(
    df["month_dt"], errors="coerce"
)

df["total_assets"] = pd.to_numeric(
    df["total_assets"], errors="coerce"
)

df = df.dropna(
    subset=["year_dt", "month_dt", "total_assets"]
)

df["year_dt"] = df["year_dt"].astype(int)
df["month_dt"] = df["month_dt"].astype(int)

# --------------------------------
# 5. Select the last observation
#    available in each year
# --------------------------------

df = df.sort_values(
    ["year_dt", "month_dt"]
)

yearly = (
    df.groupby("year_dt", as_index=False)
    .tail(1)
    .sort_values("year_dt")
    .copy()
)

yearly = yearly.rename(
    columns={
        "year_dt": "year",
        "month_dt": "month_used",
        "total_assets": "total_assets"
    }
)

# Mark full-year versus partial-year observations
yearly["period_status"] = yearly["month_used"].apply(
    lambda month: (
        "Full year (December)"
        if month == 12
        else "Partial year"
    )
)

# --------------------------------
# 6. Calculate year-on-year growth
# --------------------------------

yearly["previous_year_assets"] = (
    yearly["total_assets"].shift(1)
)

yearly["yoy_growth_percent"] = (
    yearly["total_assets"]
    .pct_change(fill_method=None)
    * 100
)

# Do not compare a partial year with a full year
partial_years = yearly["month_used"] < 12

yearly.loc[
    partial_years,
    "yoy_growth_percent"
] = float("nan")

# --------------------------------
# 7. Display the results
# --------------------------------

print("\nYEARLY ASSET SUMMARY")
print(
    yearly[
        [
            "year",
            "month_used",
            "total_assets",
            "period_status",
            "yoy_growth_percent"
        ]
    ].to_string(index=False)
)

# --------------------------------
# 8. Save the summary
# --------------------------------

summary_file = (
    output_folder / "yearly_asset_analysis.xlsx"
)

yearly.to_excel(summary_file, index=False)

yearly.to_csv(
    output_folder / "yearly_asset_analysis.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nSummary saved to:", summary_file.resolve())

# --------------------------------
# 9. Chart 1: Total assets over time
# --------------------------------

plt.figure(figsize=(10, 6))

plt.plot(
    yearly["year"],
    yearly["total_assets"],
    marker="o"
)

plt.title("Malaysian Islamic Banking Assets (2016–2026)")
plt.xlabel("Year")
plt.ylabel("Total Assets (original BNM unit)")
plt.xticks(yearly["year"], rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    output_folder / "yearly_assets_trend.png",
    dpi=300
)

plt.show()

# --------------------------------
# 10. Chart 2: Year-on-year growth
# --------------------------------

growth_data = yearly.dropna(
    subset=["yoy_growth_percent"]
)

plt.figure(figsize=(10, 6))

plt.bar(
    growth_data["year"],
    growth_data["yoy_growth_percent"]
)

plt.title("Year-on-Year Growth in Islamic Banking Assets")
plt.xlabel("Year")
plt.ylabel("Growth (%)")
plt.xticks(growth_data["year"], rotation=45)
plt.axhline(y=0, linewidth=1)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    output_folder / "yearly_assets_growth.png",
    dpi=300
)

plt.show()

print("\nBoth charts have been saved!")
print("Output folder:", output_folder.resolve())
