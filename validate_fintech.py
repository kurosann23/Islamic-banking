
from pathlib import Path
import pandas as pd

file_path = Path(
    "data/fintech/malaysia_payment_systems_2016_2026.csv"
)

if not file_path.exists():
    raise FileNotFoundError(f"Cannot find: {file_path.resolve()}")

df = pd.read_csv(file_path)

required_columns = {"date", "system", "volume", "value"}
missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df["system"] = df["system"].astype("string").str.lower().str.strip()

print("=" * 55)
print("MALAYSIA FINTECH DATA QUALITY REPORT")
print("=" * 55)

# 1. Basic information
print("\n1. DATASET OVERVIEW")
print("Rows:", len(df))
print("Columns:", list(df.columns))
print("First date:", df["date"].min())
print("Last date:", df["date"].max())

# 2. Missing data
print("\n2. MISSING VALUES")
print(df.isna().sum().to_string())

# 3. Duplicate date/system combinations
duplicates = df.duplicated(
    subset=["date", "system"], keep=False
)

print("\n3. DUPLICATE DATE-SYSTEM ROWS:", int(duplicates.sum()))

if duplicates.any():
    print(df.loc[duplicates].sort_values(["date", "system"]).to_string(index=False))

# 4. Expected payment system codes
expected_systems = {
    "dd", "fpx", "ibg", "jompay", "rentas", "rpp"
}

actual_systems = set(df["system"].dropna().unique())

print("\n4. PAYMENT SYSTEM CODES")
print("Found:", sorted(actual_systems))
print("Unexpected:", sorted(actual_systems - expected_systems))
print("Missing expected codes:", sorted(expected_systems - actual_systems))

# 5. Invalid numeric values
print("\n5. INVALID NUMERIC VALUES")
print("Negative transaction counts:", int((df["volume"] < 0).sum()))
print("Negative transaction values:", int((df["value"] < 0).sum()))

# 6. Monthly coverage per payment system
print("\n6. MONTHLY COVERAGE")

valid_dates = df.dropna(subset=["date", "system"]).copy()
valid_dates["month"] = valid_dates["date"].dt.to_period("M")

for system in sorted(valid_dates["system"].unique()):
    system_data = valid_dates[valid_dates["system"] == system]
    months = sorted(system_data["month"].unique())

    if not months:
        continue

    expected_months = pd.period_range(
        start=months[0],
        end=months[-1],
        freq="M"
    )

    missing_months = expected_months.difference(months)

    print(
        f"{system}: {len(months)} observed months; "
        f"{len(missing_months)} missing months"
    )

    if len(missing_months) > 0:
        print("   Missing:", ", ".join(map(str, missing_months)))

# 7. Check how many months are available in each year
print("\n7. MONTHS AVAILABLE PER YEAR")

yearly_coverage = (
    valid_dates.groupby(
        [valid_dates["date"].dt.year, "system"]
    )["month"]
    .nunique()
    .unstack(fill_value=0)
)

print(yearly_coverage.to_string())

print("\nValidation report completed.")
