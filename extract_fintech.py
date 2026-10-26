
import pandas as pd
import requests
from pathlib import Path

# 1. Official Malaysian payment statistics dataset
url = (
    "https://storage.data.gov.my/"
    "finsector/payments/systems.csv"
)

# 2. Create output folder
output_folder = Path("data/fintech")
output_folder.mkdir(parents=True, exist_ok=True)

print("Downloading official payment data...")

# 3. Download the CSV file
response = requests.get(url, timeout=60)
response.raise_for_status()

# 4. Read the downloaded CSV using pandas
from io import BytesIO

df = pd.read_csv(BytesIO(response.content))

print("\nDownload successful!")
print("Number of records:", len(df))
print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head().to_string(index=False))

# 5. Convert date column to proper dates
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# 6. Convert numeric columns
df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

# 7. Filter the requested research period
start_date = "2016-01-01"
end_date = "2026-12-31"

df = df[
    (df["date"] >= start_date)
    & (df["date"] <= end_date)
].copy()

# 8. Sort the data
df = df.sort_values(["date", "system"])

# 9. Export the full filtered dataset
df.to_csv(
    output_folder / "malaysia_payment_systems_2016_2026.csv",
    index=False,
    encoding="utf-8-sig"
)

df.to_excel(
    output_folder / "malaysia_payment_systems_2016_2026.xlsx",
    index=False
)

print("\nFiltered data exported successfully!")
print("Records:", len(df))

if not df.empty:
    print("First reporting date:", df["date"].min())
    print("Last reporting date:", df["date"].max())

    print("\nRecords by payment system:")
    print(df["system"].value_counts().to_string())

    print("\nRecords by year:")
    print(df.groupby(df["date"].dt.year).size().to_string())

print("\nOutput folder:", output_folder.resolve())
