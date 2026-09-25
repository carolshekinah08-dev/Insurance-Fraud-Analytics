
import os
from pathlib import Path

import psycopg2
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORENSIC_OUTPUT_DIR = PROJECT_ROOT / "data" / "forensic_outputs"

print("=" * 70)
print("DAY 3 - TASK 24: FETCH MASTER VIEW")
print("=" * 70)

# Connect ONLY to the existing PostgreSQL database.
# This script does NOT load the Parquet files.
conn = psycopg2.connect(
    host="localhost",
    port=54321,
    database="nexlyra_insurance",
    user="postgres",
    password=os.getenv("NEXLYRA_DB_PASSWORD")
)

print("Connected to PostgreSQL successfully.")
print("Fetching existing vw_powerbi_dataset...")

df = pd.read_sql_query(
    'SELECT * FROM vw_powerbi_dataset',
    conn
)

conn.close()

print("\n" + "=" * 70)
print("TASK 24 VERIFICATION")
print("=" * 70)

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Shape:", df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nTask 24 complete.")
print("\n" + "=" * 70)
print("DAY 3 - TASK 25: NULL CHECK")
print("=" * 70)

null_counts = df.isnull().sum()

null_counts = null_counts[null_counts > 0].sort_values(ascending=False)

print("\nColumns containing NULL values:")

if null_counts.empty:
    print("No NULL values found.")
else:
    print(null_counts)

print("\nTotal NULL values:", int(df.isnull().sum().sum()))

print("\nTask 25 complete.")
print("\n" + "=" * 70)
print("DAY 3 - TASK 26: DATA TYPE VERIFICATION")
print("=" * 70)

print("\nData types:")
print(df.dtypes)

print("\nDataFrame information:")
df.info()

print("\nTask 26 complete.")
print("\n" + "=" * 70)
print("DAY 3 - TASK 27: SAVE POWER BI DATASET")
print("=" * 70)

output_file = FORENSIC_OUTPUT_DIR / "powerbi_ready.csv"

df.to_csv(
    output_file,
    index=False
)

print(f"\nSaved successfully: {output_file}")

print("\nFile verification:")
import os

file_size_mb = os.path.getsize(output_file) / (1024 * 1024)

print(f"File size: {file_size_mb:.2f} MB")
print(f"Rows saved: {len(df):,}")
print(f"Columns saved: {len(df.columns)}")

print("\nTask 27 complete.")
