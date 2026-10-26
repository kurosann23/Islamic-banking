
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# 1. Set file paths
input_file = Path(
    "data/fintech/malaysia_payment_systems_2016_2026.csv"
)

output_folder = Path("data/fintech/analysis")
output_folder.mkdir(parents=True, exist_ok=True)

# 2. Load the downloaded data
df = pd.read_csv(input_file)

# 3. Clean the columns
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df.dropna(subset=["date", "system", "volume", "value"])
df = df.sort_values(["date", "system"])

# The source data starts in 2019, not 2016.
df = df[
    (df["date"] >= "2016-01-01")
    & (df["date"] <= "2026-12-31")
].copy()

if df.empty:
    raise ValueError(
        "No usable data found. Check the CSV file path and contents."
    )

# 4. Display a basic data report
print("=" * 50)
print("MALAYSIA FINTECH PAYMENT ANALYSIS")
print("=" * 50)

print("\nDataset shape:", df.shape)
print("First month:", df["date"].min().strftime("%Y-%m"))
print("Last month:", df["date"].max().strftime("%Y-%m"))

print("\nPayment systems:")
print(df["system"].value_counts().to_string())

# 5. Save a cleaned copy
df.to_csv(
    output_folder / "cleaned_payment_data.csv",
    index=False,
    encoding="utf-8-sig"
)

# 6. Monthly totals by payment system
monthly = (
    df.groupby(["date", "system"], as_index=False)
    .agg(
        volume=("volume", "sum"),
        value=("value", "sum")
    )
)

monthly.to_excel(
    output_folder / "monthly_payment_summary.xlsx",
    index=False
)

# RENTAS is a high-value payment system.
# Exclude it from retail-system charts so the scale is easier to read.
retail = monthly[monthly["system"] != "rentas"].copy()

# 7. Chart 1: Monthly transaction volume
volume_pivot = retail.pivot(
    index="date",
    columns="system",
    values="volume"
).fillna(0)

ax = volume_pivot.plot(figsize=(12, 6))
ax.set_title("Malaysia Payment Systems: Monthly Transaction Volume")
ax.set_xlabel("Month")
ax.set_ylabel("Number of Transactions")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    output_folder / "01_monthly_transaction_volume.png",
    dpi=200
)
plt.close()

# 8. Chart 2: Monthly transaction value
value_pivot = retail.pivot(
    index="date",
    columns="system",
    values="value"
).fillna(0) / 1_000_000_000

ax = value_pivot.plot(figsize=(12, 6))
ax.set_title("Malaysia Payment Systems: Monthly Transaction Value")
ax.set_xlabel("Month")
ax.set_ylabel("Transaction Value (RM billion)")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    output_folder / "02_monthly_transaction_value.png",
    dpi=200
)
plt.close()

# 9. Annual totals by system
annual = (
    df.assign(year=df["date"].dt.year)
    .groupby(["year", "system"], as_index=False)
    .agg(
        volume=("volume", "sum"),
        value=("value", "sum")
    )
)

annual.to_excel(
    output_folder / "annual_payment_summary.xlsx",
    index=False
)

annual_retail = annual[annual["system"] != "rentas"]

annual_volume = annual_retail.pivot(
    index="year",
    columns="system",
    values="volume"
).fillna(0)

ax = annual_volume.plot(kind="bar", figsize=(12, 6))
ax.set_title("Annual Transaction Volume by Payment System")
ax.set_xlabel("Year")
ax.set_ylabel("Number of Transactions")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(
    output_folder / "03_annual_transaction_volume.png",
    dpi=200
)
plt.close()

# 10. Chart 4: RENTAS transaction value separately
rentas = monthly[monthly["system"] == "rentas"].copy()

if not rentas.empty:
    plt.figure(figsize=(12, 6))
    plt.plot(
        rentas["date"],
        rentas["value"] / 1_000_000_000,
        marker="o"
    )
    plt.title("RENTAS: Monthly Transaction Value")
    plt.xlabel("Month")
    plt.ylabel("Transaction Value (RM billion)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        output_folder / "04_rentas_transaction_value.png",
        dpi=200
    )
    plt.close()

# 11. Export the full cleaned dataset and annual summary to Excel
with pd.ExcelWriter(
    output_folder / "fintech_payment_analysis.xlsx"
) as writer:
    df.to_excel(writer, sheet_name="Cleaned Data", index=False)
    monthly.to_excel(writer, sheet_name="Monthly Summary", index=False)
    annual.to_excel(writer, sheet_name="Annual Summary", index=False)

print("\nAnalysis completed successfully!")
print("\nFiles saved in:")
print(output_folder.resolve())

print("\nGenerated charts:")
for file in sorted(output_folder.glob("*.png")):
    print("-", file.name)

print("\nAnnual summary:")
print(annual.to_string(index=False))
