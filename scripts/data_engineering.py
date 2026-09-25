import pandas as pd
import numpy as np
import re
import base64
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_FILE = DATA_DIR / "raw" / "nexlyra_global_real_estate_1M_carol_elite.csv"
PROCESSED_DIR = DATA_DIR / "processed"
FORENSIC_OUTPUT_DIR = DATA_DIR / "forensic_outputs"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FORENSIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PROJECT 2
# PHANTOM DISASTER CLAIMS & INSURANCE PREMIUM EMBEZZLEMENT
#
# DAY 1 - TASKS 1 TO 36
# ============================================================


# ============================================================
# TASK 1 & 2
# LOAD THE 1 MILLION ROW CSV
# ============================================================

CSV_PATH = RAW_DATA_FILE

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

df = pd.read_csv(
    CSV_PATH,
    low_memory=False
)

print("Dataset loaded successfully!")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Shape:", df.shape)


# ============================================================
# TASK 3
# MEMORY PROFILING & NUMERIC DOWNCASTING
# ============================================================

print("\n" + "=" * 70)
print("TASK 3 - MEMORY OPTIMIZATION")
print("=" * 70)

memory_before = (
    df.memory_usage(deep=True).sum() / 1024**2
)

print(
    f"Memory BEFORE optimization: "
    f"{memory_before:.2f} MB"
)


for column in df.columns:

    # Downcast integer columns
    if pd.api.types.is_integer_dtype(df[column]):

        df[column] = pd.to_numeric(
            df[column],
            downcast="integer"
        )

    # Downcast floating-point columns
    elif pd.api.types.is_float_dtype(df[column]):

        df[column] = pd.to_numeric(
            df[column],
            downcast="float"
        )


memory_after = (
    df.memory_usage(deep=True).sum() / 1024**2
)

memory_saved = memory_before - memory_after

percentage_saved = (
    memory_saved / memory_before
) * 100


print(
    f"Memory AFTER optimization: "
    f"{memory_after:.2f} MB"
)

print(
    f"Memory SAVED: "
    f"{memory_saved:.2f} MB"
)

print(
    f"Memory REDUCTION: "
    f"{percentage_saved:.2f}%"
)


# ============================================================
# TASK 4 & 5
# MIXED DATE PARSER
#
# Incident_Date contains:
# - Normal dates: 2022-01-06
# - Hex timestamps: 0x5db23b00
# ============================================================

print("\n" + "=" * 70)
print("TASK 4 & 5 - INCIDENT DATE PARSING")
print("=" * 70)


def parse_incident_date(value):

    try:

        # Missing value
        if pd.isna(value):
            return pd.NaT

        value = str(value).strip()

        # ----------------------------------------
        # HEXADECIMAL UNIX TIMESTAMP
        # ----------------------------------------

        if value.lower().startswith("0x"):

            # Convert hexadecimal to base-10
            timestamp = int(value, 16)

            # Convert Unix seconds to datetime
            return pd.to_datetime(
                timestamp,
                unit="s"
            )

        # ----------------------------------------
        # STANDARD DATE
        # ----------------------------------------

        return pd.to_datetime(value)

    except (
        ValueError,
        TypeError,
        OverflowError
    ):

        return pd.NaT


df["Incident_Date"] = df["Incident_Date"].apply(
    parse_incident_date
)

print(
    "Incident_Date datatype:",
    df["Incident_Date"].dtype
)


# ============================================================
# TASK 6
# VERIFY NO NaT VALUES
# ============================================================

print("\n" + "=" * 70)
print("TASK 6 - CHECK INVALID DATES")
print("=" * 70)

nat_count = df["Incident_Date"].isna().sum()

print("NaT values after parsing:", nat_count)


# The source file contains one genuinely blank Incident_Date.
# Since the task requires a complete datetime column, use the
# median valid incident date as a neutral temporal imputation.

if nat_count > 0:

    median_incident_date = df["Incident_Date"].dropna().median()

    df["Incident_Date"] = df["Incident_Date"].fillna(
        median_incident_date
    )

    print(
        "Missing Incident_Date values filled using "
        "the median valid incident date."
    )


# Final validation
nat_count = df["Incident_Date"].isna().sum()

print(
    "Final NaT count:",
    nat_count
)


# ============================================================
# TASK 7
# EXTRACT YEAR, MONTH AND QUARTER
# ============================================================

print("\n" + "=" * 70)
print("TASK 7 - DATE COMPONENTS")
print("=" * 70)

df["Year"] = df["Incident_Date"].dt.year.astype("int16")

df["Month"] = df["Incident_Date"].dt.month.astype("int8")

df["Quarter"] = (
    df["Incident_Date"]
    .dt.quarter
    .astype("int8")
)

print("Year, Month and Quarter columns created.")


# ============================================================
# TASK 8
# CORRUPTED JSON
#
# Some rows contain:
#
# "payout_routing" {
#
# instead of:
#
# "payout_routing": {
#
# Therefore json.loads() cannot reliably be used.
# ============================================================

print("\n" + "=" * 70)
print("TASK 8 - CORRUPTED JSON")
print("=" * 70)

print(
    "Corrupted JSON will be handled using regex extraction."
)


# ============================================================
# TASK 9
# REGEX EXTRACTION FUNCTION
# ============================================================

print("\n" + "=" * 70)
print("TASK 9 - REGEX JSON PARSER")
print("=" * 70)


def regex_extract(pattern, value):

    try:

        if pd.isna(value):
            return None

        match = re.search(
            pattern,
            str(value)
        )

        if match:
            return match.group(1)

        return None

    except (
        TypeError,
        AttributeError,
        re.error
    ):

        return None


# ============================================================
# TASK 10
# EXTRACT INCIDENT CLASSIFICATION
# ============================================================

print("\n" + "=" * 70)
print("TASK 10 - INCIDENT CLASSIFICATION")
print("=" * 70)


df["Incident_Classification"] = (
    df["Insurance_Metadata_JSON"]
    .apply(
        lambda x: regex_extract(
            r'"incident_classification"\s*:\s*"([^"]*)"',
            x
        )
    )
)

print(
    "Incident_Classification extracted."
)


# ============================================================
# TASK 11
# EXTRACT PAYOUT AUTHORIZED
# ============================================================

print("\n" + "=" * 70)
print("TASK 11 - PAYOUT AUTHORIZED")
print("=" * 70)


df["Payout_Authorized"] = pd.to_numeric(
    df["Insurance_Metadata_JSON"].apply(
        lambda x: regex_extract(
            r'"payout_authorized"\s*:\s*([-+]?\d+(?:\.\d+)?)',
            x
        )
    ),
    errors="coerce"
)

print(
    "Payout_Authorized extracted."
)

print(
    "Missing payout values:",
    df["Payout_Authorized"].isna().sum()
)


# ============================================================
# TASK 12
# EXTRACT DEEPLY NESTED CONTRACTOR AND GRATUITY
# ============================================================

print("\n" + "=" * 70)
print("TASK 12 - NESTED INSURANCE DATA")
print("=" * 70)


df["Contractor_A85"] = (
    df["Insurance_Metadata_JSON"]
    .apply(
        lambda x: regex_extract(
            r'"contractor_a85"\s*:\s*"([^"]*)"',
            x
        )
    )
)


df["Adjuster_Gratuity"] = pd.to_numeric(
    df["Insurance_Metadata_JSON"].apply(
        lambda x: regex_extract(
            r'"adjuster_gratuity"\s*:\s*([-+]?\d+(?:\.\d+)?)',
            x
        )
    ),
    errors="coerce"
)

print("Contractor_A85 extracted.")
print("Adjuster_Gratuity extracted.")


# ============================================================
# TASK 13 & 14
# ASCII85 / BASE85 DECODING
# ============================================================

print("\n" + "=" * 70)
print("TASK 13 & 14 - ASCII85 DECODING")
print("=" * 70)


def decode_contractor(value):

    try:

        if pd.isna(value):
            return None

        decoded = base64.a85decode(
            str(value)
        )

        return decoded.decode(
            "utf-8",
            errors="replace"
        )

    except (
        ValueError,
        TypeError,
        base64.binascii.Error
    ):

        return None


df["Decoded_Contractor"] = (
    df["Contractor_A85"]
    .apply(decode_contractor)
)

print("Base85 decoding completed.")

print(
    "\nDecoded contractor examples:"
)

print(
    df["Decoded_Contractor"]
    .value_counts()
    .head()
)


# ============================================================
# TASK 15 & 16
# CURRENCY CONVERSION TO USD
# ============================================================

print("\n" + "=" * 70)
print("TASK 15 & 16 - USD CONVERSION")
print("=" * 70)


# Static exchange rates:
#
# Currency -> USD
#
# USD = 1.000000
# EUR = 1.111111
# GBP = 1.333333
# CAD = 0.740741
#
# These rates match the fixed currency relationships present
# in the supplied dataset.

exchange_rates = {
    "USD": 1.000000,
    "EUR": 1.1111111111,
    "GBP": 1.3333333333,
    "CAD": 0.7407407407
}


df["Exchange_Rate_USD"] = (
    df["Currency_Code"]
    .map(exchange_rates)
)


# Check for unknown currencies
unknown_currency_count = (
    df["Exchange_Rate_USD"].isna().sum()
)

if unknown_currency_count > 0:

    print(
        "WARNING:",
        unknown_currency_count,
        "rows have unknown Currency_Code."
    )


# Valuation -> USD
df["Valuation_USD"] = (
    df["Valuation_Local"]
    * df["Exchange_Rate_USD"]
)


# Current premium -> USD
df["Current_Premium_USD"] = (
    df["Current_Premium_Local"]
    * df["Exchange_Rate_USD"]
)


print("Valuation_USD created.")
print("Current_Premium_USD created.")


# ============================================================
# TASK 17
# PREMIUM SPIKE
# ============================================================

print("\n" + "=" * 70)
print("TASK 17 - PREMIUM SPIKE")
print("=" * 70)


df["Premium_Spike_USD"] = (
    df["Current_Premium_USD"]
    - df["Base_Premium_USD"]
)


# ============================================================
# TASK 18
# PAYOUT TO VALUE RATIO
# ============================================================

print("\n" + "=" * 70)
print("TASK 18 - PAYOUT TO VALUE RATIO")
print("=" * 70)


df["Payout_to_Value_Ratio"] = np.where(
    df["Valuation_USD"] != 0,
    df["Payout_Authorized"] / df["Valuation_USD"],
    0.0
)


# ============================================================
# TASK 19
# PHANTOM CLAIM SUSPECT
# ============================================================

print("\n" + "=" * 70)
print("TASK 19 - PHANTOM CLAIM FLAG")
print("=" * 70)


df["Phantom_Claim_Suspect"] = (
    (
        df["Premium_Spike_USD"]
        > (df["Base_Premium_USD"] * 2)
    )
    &
    (
        df["Payout_Authorized"] > 50000
    )
).astype("int8")


phantom_count = (
    df["Phantom_Claim_Suspect"]
    .sum()
)

print(
    "Phantom Claim Suspect rows:",
    phantom_count
)


# ============================================================
# TASK 20
# ADJUSTER KICKBACK RATIO
# ============================================================

print("\n" + "=" * 70)
print("TASK 20 - ADJUSTER KICKBACK RATIO")
print("=" * 70)


df["Adjuster_Kickback_Ratio"] = np.where(
    df["Payout_Authorized"] != 0,
    df["Adjuster_Gratuity"]
    / df["Payout_Authorized"],
    0.0
)


# ============================================================
# TASK 21
# TOTAL FINANCIAL DAMAGE
# ============================================================

print("\n" + "=" * 70)
print("TASK 21 - TOTAL FINANCIAL DAMAGE")
print("=" * 70)


df["Total_Financial_Damage_USD"] = (
    df["Payout_Authorized"]
    + df["Premium_Spike_USD"]
)


# ============================================================
# TASK 22
# TOP 5 ADJUSTERS BY GRATUITY
# ============================================================

print("\n" + "=" * 70)
print("TASK 22 - TOP 5 ADJUSTERS")
print("=" * 70)


top_5_adjusters = (
    df.groupby("Adjuster_ID")["Adjuster_Gratuity"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
)


print(
    top_5_adjusters
)


# ============================================================
# TASK 23
# TOP CONTRACTORS BY AUTHORIZED PAYOUT
# ============================================================

print("\n" + "=" * 70)
print("TASK 23 - TOP CONTRACTORS")
print("=" * 70)


top_contractors = (
    df.groupby("Decoded_Contractor")["Payout_Authorized"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)


print(
    top_contractors
)


# ============================================================
# TASK 24
# AVERAGE PREMIUM SPIKE FOR PHANTOM CLAIMS
# ============================================================

print("\n" + "=" * 70)
print("TASK 24 - AVERAGE PHANTOM PREMIUM SPIKE")
print("=" * 70)


phantom_average_spike = (
    df.loc[
        df["Phantom_Claim_Suspect"] == 1,
        "Premium_Spike_USD"
    ]
    .mean()
)


print(
    "Average Premium Spike for Phantom Claims:",
    phantom_average_spike
)


# ============================================================
# TASK 25
# DUPLICATE PROPERTY_ID + INCIDENT_DATE
# ============================================================

print("\n" + "=" * 70)
print("TASK 25 - DUPLICATE RECORDS")
print("=" * 70)


duplicate_count = (
    df.duplicated(
        subset=[
            "Property_ID",
            "Incident_Date"
        ],
        keep="first"
    )
    .sum()
)


print(
    "Duplicate rows found:",
    duplicate_count
)


df = df.drop_duplicates(
    subset=[
        "Property_ID",
        "Incident_Date"
    ],
    keep="first"
).reset_index(drop=True)


print(
    "Rows after duplicate removal:",
    len(df)
)


# ============================================================
# TASK 26
# IMPUTE NUMERICAL MISSING VALUES USING MEDIAN
# ============================================================

print("\n" + "=" * 70)
print("TASK 26 - NUMERICAL IMPUTATION")
print("=" * 70)


numeric_columns = df.select_dtypes(
    include=np.number
).columns


for column in numeric_columns:

    missing_count = df[column].isna().sum()

    if missing_count > 0:

        median_value = df[column].median()

        df[column] = df[column].fillna(
            median_value
        )

        print(
            f"{column}: "
            f"{missing_count} values filled with median."
        )


# ============================================================
# TASK 27
# IMPUTE CATEGORICAL VALUES WITH "UNKNOWN"
# ============================================================

print("\n" + "=" * 70)
print("TASK 27 - CATEGORICAL IMPUTATION")
print("=" * 70)


string_columns = df.select_dtypes(
    include=["object", "string"]
).columns


for column in string_columns:

    missing_count = df[column].isna().sum()

    if missing_count > 0:

        df[column] = df[column].fillna(
            "Unknown"
        )

        print(
            f"{column}: "
            f"{missing_count} values filled with Unknown."
        )


# ============================================================
# TASK 28
# STRIP WHITESPACE FROM ALL STRING COLUMNS
# ============================================================

print("\n" + "=" * 70)
print("TASK 28 - STRING CLEANING")
print("=" * 70)


string_columns = df.select_dtypes(
    include=["object", "string"]
).columns


for column in string_columns:

    df[column] = df[column].str.strip()


print(
    "Leading/trailing whitespace removed."
)


# ============================================================
# TASK 29
# UPPERCASE COLUMN NAMES WITH UNDERSCORES
# ============================================================

print("\n" + "=" * 70)
print("TASK 29 - STANDARDIZE COLUMN NAMES")
print("=" * 70)


def clean_column_name(column):

    column = str(column)

    # Replace non-alphanumeric characters with _
    column = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        column
    )

    # Remove leading/trailing underscores
    column = column.strip("_")

    # Convert to uppercase
    return column.upper()


df.columns = [
    clean_column_name(column)
    for column in df.columns
]


print(
    "Column names standardized."
)

print(
    "\nFinal column names:"
)

print(
    df.columns.tolist()
)


# ============================================================
# FROM THIS POINT ON, COLUMN NAMES ARE UPPERCASE
# ============================================================


# ============================================================
# TASK 30
# ABSOLUTE TOTAL PAYOUT
# ============================================================

print("\n" + "=" * 70)
print("TASK 30 - TOTAL AUTHORIZED PAYOUT")
print("=" * 70)


total_payout = abs(
    df["PAYOUT_AUTHORIZED"].sum()
)


print(
    f"Absolute total authorized payout: "
    f"${total_payout:,.2f}"
)


# ============================================================
# TASK 31
# ASSERT NO NEGATIVE PREMIUMS
# ============================================================

print("\n" + "=" * 70)
print("TASK 31 - PREMIUM VALIDATION")
print("=" * 70)


assert (
    df["CURRENT_PREMIUM_LOCAL"] >= 0
).all(), "Negative Current_Premium_Local detected!"


assert (
    df["BASE_PREMIUM_USD"] >= 0
).all(), "Negative Base_Premium_USD detected!"


assert (
    df["CURRENT_PREMIUM_USD"] >= 0
).all(), "Negative Current_Premium_USD detected!"


print(
    "PASS: No negative premium values found."
)


# ============================================================
# TASK 32
# MANAGER -> TOTAL AUTHORIZED PAYOUT DICTIONARY
# ============================================================

print("\n" + "=" * 70)
print("TASK 32 - MANAGER PAYOUT SUMMARY")
print("=" * 70)


manager_payout_summary = (
    df.groupby("MANAGER_ID")["PAYOUT_AUTHORIZED"]
    .sum()
    .to_dict()
)


print(
    "Number of managers:",
    len(manager_payout_summary)
)


# ============================================================
# TASK 33
# EXPORT MANAGER FRAUD SUMMARY JSON
# ============================================================

print("\n" + "=" * 70)
print("TASK 33 - EXPORT JSON")
print("=" * 70)


with open(
    FORENSIC_OUTPUT_DIR / "manager_fraud_summary.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        manager_payout_summary,
        file,
        indent=4
    )


print(
    "Created: manager_fraud_summary.json"
)


# ============================================================
# TASK 34 & 35
# PARTITIONED PARQUET BY COUNTRY_CODE
# ============================================================

print("\n" + "=" * 70)
print("TASK 34 & 35 - PARTITIONED PARQUET")
print("=" * 70)


PARQUET_PATH = PROCESSED_DIR / "insurance_partitioned_parquet"


# Create directory if it doesn't exist
PARQUET_PATH.mkdir(
    parents=True,
    exist_ok=True
)


df.to_parquet(
    PARQUET_PATH,
    engine="pyarrow",
    partition_cols=["COUNTRY_CODE"],
    index=False
)


print(
    "Partitioned Parquet dataset created at:",
    PARQUET_PATH
)


# ============================================================
# TASK 36
# EXPORT UP TO 150,000 PHANTOM CLAIM ROWS
# ============================================================

print("\n" + "=" * 70)
print("TASK 36 - INSURANCE AUDIT CSV")
print("=" * 70)


phantom_claims = df[
    df["PHANTOM_CLAIM_SUSPECT"] == 1
]


# The assignment asks for a 150,000-row subset.
# If fewer than 150,000 rows are flagged, export all
# available flagged rows.

audit_subset = phantom_claims.head(
    150000
)


audit_subset.to_csv(
    PROCESSED_DIR / "insurance_audit.csv",
    index=False
)


print(
    "Flagged rows available:",
    len(phantom_claims)
)

print(
    "Rows exported:",
    len(audit_subset)
)

print(
    "Created: insurance_audit.csv"
)


# ============================================================
# FINAL PROJECT CHECK
# ============================================================

print("\n" + "=" * 70)
print("DAY 1 COMPLETE")
print("=" * 70)

print(
    "Final dataset shape:",
    df.shape
)

print(
    "Final memory usage:",
    f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
)

print(
    "\nOutput files created:"
)

print(
    "1. manager_fraud_summary.json"
)

print(
    "2. insurance_partitioned_parquet/"
)

print(
    "3. insurance_audit.csv"
)

print("\nAll Day 1 tasks completed.")
# ============================================================
# DAY 3 - TASK 2
# LOAD PARTITIONED PARQUET INTO POSTGRESQL
# ============================================================

import psycopg2
import pyarrow.parquet as pq

DB_CONFIG = {
    "host": "localhost",
    "port": 54321,
    "database": "nexlyra_insurance",
    "user": "postgres",
    "password": os.getenv("NEXLYRA_DB_PASSWORD")
}

PARQUET_ROOT = PARQUET_PATH

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Create the table using the Parquet schema
sample_file = next(PARQUET_ROOT.rglob("*.parquet"))
sample_table = pq.read_table(sample_file)

columns = sample_table.schema.names

column_definitions = []

for column in columns:
    column_definitions.append(f'"{column}" TEXT')

create_table_sql = f"""
CREATE TABLE IF NOT EXISTS reit_portfolio (
    {", ".join(column_definitions)}
);
"""

cursor.execute(create_table_sql)
conn.commit()

print("Table reit_portfolio created.")

# Load every Parquet partition
parquet_files = list(PARQUET_ROOT.rglob("*.parquet"))

for parquet_file in parquet_files:

    print(f"Loading: {parquet_file}")

    table = pq.read_table(parquet_file)
    data = table.to_pandas()

    columns_sql = ", ".join(f'"{c}"' for c in data.columns)
    placeholders = ", ".join(["%s"] * len(data.columns))

    insert_sql = f"""
        INSERT INTO reit_portfolio ({columns_sql})
        VALUES ({placeholders})
    """

    rows = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in data.itertuples(index=False, name=None)
    ]

    cursor.executemany(insert_sql, rows)
    conn.commit()

print("All Parquet partitions loaded successfully.")

cursor.close()
conn.close()
print("DAY 3 TASK 2 COMPLETE")

# ============================================================
# DAY 3 - FIX COUNTRY_CODE
# Populate COUNTRY_CODE from the Parquet partition folders
# ============================================================

import psycopg2
import pyarrow.parquet as pq
from pathlib import Path

# ------------------------------------------------------------
# PostgreSQL connection
# ------------------------------------------------------------

conn = psycopg2.connect(
    host="localhost",
    port=54321,
    database="nexlyra_insurance",
    user="postgres",
    password=os.getenv("NEXLYRA_DB_PASSWORD")
)

cur = conn.cursor()

# ------------------------------------------------------------
# Location of partitioned Parquet files
# ------------------------------------------------------------

root = PARQUET_PATH

# Check that the folder exists
if not root.exists():
    raise FileNotFoundError(
        "insurance_partitioned_parquet folder was not found."
    )

# ------------------------------------------------------------
# Process each country partition
# ------------------------------------------------------------

for partition in sorted(root.glob("COUNTRY_CODE=*")):

    # Extract country code from folder name
    # Example:
    # COUNTRY_CODE=US -> US
    country = partition.name.split("=", 1)[1]

    # Find the Parquet file inside the partition
    parquet_files = list(partition.glob("*.parquet"))

    if not parquet_files:
        print(f"No Parquet file found for {country}")
        continue

    parquet_file = parquet_files[0]

    print(f"Processing {country}...")
    print(f"File: {parquet_file}")

    # Read only PROPERTY_ID
    table = pq.read_table(
        parquet_file,
        columns=["PROPERTY_ID"]
    )

    property_ids = table.column("PROPERTY_ID").to_pylist()

    # --------------------------------------------------------
    # Update PostgreSQL
    # --------------------------------------------------------

    cur.execute(
        """
        UPDATE reit_portfolio
        SET "COUNTRY_CODE" = %s
        WHERE "PROPERTY_ID" = ANY(%s)
        """,
        (country, property_ids)
    )

    print(
        f"{country}: {cur.rowcount:,} rows updated"
    )

    # Save each country update
    conn.commit()

# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

cur.execute(
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT("COUNTRY_CODE") AS rows_with_country,
        COUNT(DISTINCT "COUNTRY_CODE") AS countries
    FROM reit_portfolio
    """
)

verification = cur.fetchone()

print()
print("==========================================")
print("COUNTRY CODE VERIFICATION")
print("==========================================")
print(f"Total rows:          {verification[0]:,}")
print(f"Rows with country:   {verification[1]:,}")
print(f"Distinct countries:  {verification[2]}")
print("==========================================")

# ------------------------------------------------------------
# Show country distribution
# ------------------------------------------------------------

cur.execute(
    """
    SELECT
        "COUNTRY_CODE",
        COUNT(*) AS row_count
    FROM reit_portfolio
    GROUP BY "COUNTRY_CODE"
    ORDER BY "COUNTRY_CODE"
    """
)

print()
print("Country distribution:")

for country_code, row_count in cur.fetchall():
    print(f"{country_code}: {row_count:,}")

# ------------------------------------------------------------
# Close connection
# ------------------------------------------------------------

cur.close()
conn.close()

print()
print("COUNTRY_CODE update completed successfully.")
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host="localhost",
    port=54321,
    database="nexlyra_insurance",
    user="postgres",
    password=os.getenv("NEXLYRA_DB_PASSWORD")
)

print("Fetching vw_powerbi_dataset...")

df = pd.read_sql(
    "SELECT * FROM vw_powerbi_dataset",
    conn
)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nFirst 5 rows:")
print(df.head())

conn.close()

print("\nFetch completed successfully.")
