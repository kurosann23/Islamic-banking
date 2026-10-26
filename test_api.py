
import requests
import pandas as pd
from pathlib import Path
import time

# BNM Islamic Banking System: Statement of Assets
BASE_URL = "https://api.bnm.gov.my/public/msb/1.7.1/year"

HEADERS = {
    "Accept": "application/vnd.BNM.API.v1+json"
}

START_YEAR = 2016
END_YEAR = 2026

all_records = []

for year in range(START_YEAR, END_YEAR + 1):
    url = f"{BASE_URL}/{year}"

    print(f"Downloading data for {year}...")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        records = result.get("data", [])

        if isinstance(records, dict):
            records = [records]

        for record in records:
            record["requested_year"] = year
            all_records.append(record)

        print(f"  Records found: {len(records)}")

    except requests.RequestException as error:
        print(f"  Error for {year}: {error}")

    time.sleep(0.2)

# Convert all records into a table
if all_records:
    df = pd.DataFrame(all_records)

    # Convert financial values into numeric columns
    for column in df.columns:
        if column.startswith(("db_", "fb_")) or column in [
            "total_assets"
        ]:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    # Create a reporting date
    if "year_dt" in df.columns and "month_dt" in df.columns:
        df["reporting_date"] = pd.to_datetime(
            df["year_dt"].astype(str)
            + "-"
            + df["month_dt"].astype(str).str.zfill(2)
            + "-01",
            errors="coerce"
        )

    # Sort by reporting date
    if "reporting_date" in df.columns:
        df = df.sort_values("reporting_date")

    # Create output folder
    output = Path("data")
    output.mkdir(exist_ok=True)

    # Export to CSV and Excel
    df.to_csv(
        output / "islamic_banking_2016_2026.csv",
        index=False,
        encoding="utf-8-sig"
    )

    df.to_excel(
        output / "islamic_banking_2016_2026.xlsx",
        index=False
    )

    print("\nExtraction completed!")
    print("Total records:", len(df))
    print("Files saved in:", output.resolve())

else:
    print("No records were retrieved. Check the API response.")

# Inspect the available categories
print("\nFinancial institution categories:")
print(df["fin_inst"].value_counts(dropna=False))

# Check number of records by year
print("\nRecords by year:")
print(df.groupby("year_dt").size())

# Check reporting months by year
print("\nReporting months by year:")
print(df.groupby("year_dt")["month_dt"].nunique())


print("\n--- CATEGORY CHECK ---")
print(df["fin_inst"].dropna().unique())

print("\n--- RECORDS PER YEAR ---")
print(df.groupby("year_dt").size())

print("\n--- MONTHS PER YEAR ---")
print(df.groupby("year_dt")["month_dt"].nunique())

print("\n--- DUPLICATE CHECK ---")
print("Duplicate rows:", df.duplicated().sum())

print("\n--- FINANCIAL INSTITUTION CATEGORIES ---")

for category in sorted(df["fin_inst"].dropna().unique()):
    print(category)

# Create a separate workbook for analysis
output = Path("data")

with pd.ExcelWriter(
    output / "islamic_banking_cleaned.xlsx",
    engine="openpyxl"
) as writer:

    # All original extracted records
    df.to_excel(
        writer,
        sheet_name="All_Data",
        index=False
    )

    # Islamic banks only
    df[
        df["fin_inst"] == "Bank-bank Islam / Islamic Banks"
    ].to_excel(
        writer,
        sheet_name="Islamic_Banks",
        index=False
    )

    # Islamic Banking Scheme
    df[
        df["fin_inst"].str.contains(
            "Skim Perbankan Islam",
            case=False,
            na=False
        )
    ].to_excel(
        writer,
        sheet_name="Islamic_Banking_Scheme",
        index=False
    )

    # Aggregate total
    df[
        df["fin_inst"].str.contains(
            "Jumlah / Total",
            case=False,
            na=False
        )
    ].to_excel(
        writer,
        sheet_name="Banking_Total",
        index=False
    )

print("\nCleaned workbook created:")
print((output / "islamic_banking_cleaned.xlsx").resolve())
