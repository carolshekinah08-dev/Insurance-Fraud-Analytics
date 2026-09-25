
import os
import subprocess
import zipfile
from pathlib import Path
import psycopg2

# ============================================================
# DAY 3 — TASKS 28–36
# Final SQL Architecture + Export + Backup
#
# IMPORTANT:
# - Does NOT load Parquet files
# - Does NOT fetch vw_powerbi_dataset
# - Does NOT rerun Tasks 24–27
# - Uses the existing PostgreSQL database
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
FORENSIC_OUTPUT_DIR = PROJECT_DIR / "data" / "forensic_outputs"
DATABASE_DIR = PROJECT_DIR / "data" / "database"

DB_NAME = "nexlyra_insurance"
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = "54321"

DB_PASSWORD = os.getenv("NEXLYRA_DB_PASSWORD")

PSQL = os.getenv("NEXLYRA_PSQL", "psql")
PG_DUMP = os.getenv("NEXLYRA_PG_DUMP", "pg_dump")

SQL_FILE = PROJECT_DIR / "insurance_fraud_queries.sql"
SCHEMA_FILE = PROJECT_DIR / "insurance_schema.sql"
BACKUP_FILE = DATABASE_DIR / "nexlyra_insurance_backup.bak"
ZIP_FILE = PROJECT_DIR / "sql_architecture.zip"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ============================================================
# TASK 28
# Verify Recursive CTE output CSV
# ============================================================

print("\n" + "=" * 70)
print("TASK 28 — FRAUD RING CSV")
print("=" * 70)

fraud_graph = PROJECT_DIR / "insurance_fraud_rings_graph.csv"

if fraud_graph.exists():
    print(f"Already exists: {fraud_graph.name}")
    print(f"Size: {fraud_graph.stat().st_size / (1024 * 1024):.2f} MB")
else:
    print("WARNING: insurance_fraud_rings_graph.csv was not found.")
    print("The file must be generated from the Recursive CTE before continuing.")


# ============================================================
# TASK 29
# Verify LEAD() / repeat claims CSV
# ============================================================

print("\n" + "=" * 70)
print("TASK 29 — REPEAT CLAIMS CSV")
print("=" * 70)

repeat_claims = PROJECT_DIR / "repeat_claims.csv"

if repeat_claims.exists():
    print(f"Already exists: {repeat_claims.name}")
    print(f"Size: {repeat_claims.stat().st_size / (1024 * 1024):.2f} MB")
else:
    print("WARNING: repeat_claims.csv was not found.")


# ============================================================
# TASK 30
# Generate Rank output
# ============================================================

print("\n" + "=" * 70)
print("TASK 30 — INTERPOL MOST WANTED ADJUSTERS")
print("=" * 70)

rank_csv = PROJECT_DIR / "interpol_most_wanted_adjusters.csv"

conn = get_connection()
cur = conn.cursor()

rank_sql = """
SELECT
    "COUNTRY_CODE",
    "ADJUSTER_ID",
    SUM(CAST("PAYOUT_AUTHORIZED" AS NUMERIC)) AS fake_payout_total,
    RANK() OVER (
        PARTITION BY "COUNTRY_CODE"
        ORDER BY
            SUM(CAST("PAYOUT_AUTHORIZED" AS NUMERIC)) DESC
    ) AS adjuster_rank
FROM reit_portfolio
WHERE "PHANTOM_CLAIM_SUSPECT"::INTEGER = 1
GROUP BY
    "COUNTRY_CODE",
    "ADJUSTER_ID"
ORDER BY
    "COUNTRY_CODE",
    adjuster_rank;
"""

cur.execute(rank_sql)
rank_rows = cur.fetchall()

with open(rank_csv, "w", encoding="utf-8", newline="") as f:
    f.write(
        "COUNTRY_CODE,ADJUSTER_ID,fake_payout_total,adjuster_rank\n"
    )

    for row in rank_rows:
        country, adjuster, payout, rank = row
        f.write(
            f'"{country}","{adjuster}",{payout},{rank}\n'
        )

print(f"Saved: {rank_csv.name}")
print(f"Rows: {len(rank_rows):,}")


# ============================================================
# TASKS 31 + 32
# Save ALL SQL architecture queries
# with business-logic comments
# ============================================================

print("\n" + "=" * 70)
print("TASKS 31–32 — SQL ARCHITECTURE FILE")
print("=" * 70)

sql_content = r"""
-- ============================================================
-- NEXLYRA INSURANCE — DAY 3 SQL ARCHITECTURE
-- Tasks 1–23
--
-- This file documents the SQL architecture used to investigate
-- insurance fraud, collusion, risk concentration and financial
-- damage.
-- ============================================================


-- ============================================================
-- TASK 3
-- Basic row-count validation
-- Business logic:
-- Confirms that the expected 1M property records exist.
-- ============================================================

SELECT COUNT(*) AS total_rows
FROM reit_portfolio;


-- ============================================================
-- TASK 4
-- CTE: classified claims
-- Business logic:
-- Isolates records with an incident classification for
-- downstream insurance-claim analysis.
-- ============================================================

WITH classified_claims AS (
    SELECT *
    FROM reit_portfolio
    WHERE "INCIDENT_CLASSIFICATION" IS NOT NULL
)
SELECT *
FROM classified_claims;


-- ============================================================
-- TASK 5
-- LEAD() repeat-claim analysis
-- Business logic:
-- Looks at the next claim filed by the same manager and
-- checks whether the same adjuster handled both claims.
-- ============================================================

WITH claim_sequence AS (
    SELECT
        "PROPERTY_ID",
        "INCIDENT_DATE",
        "MANAGER_ID",
        "ADJUSTER_ID",
        "PAYOUT_AUTHORIZED",

        LEAD("PROPERTY_ID") OVER (
            PARTITION BY "MANAGER_ID"
            ORDER BY "INCIDENT_DATE", "PROPERTY_ID"
        ) AS next_property_id,

        LEAD("INCIDENT_DATE") OVER (
            PARTITION BY "MANAGER_ID"
            ORDER BY "INCIDENT_DATE", "PROPERTY_ID"
        ) AS next_incident_date,

        LEAD("ADJUSTER_ID") OVER (
            PARTITION BY "MANAGER_ID"
            ORDER BY "INCIDENT_DATE", "PROPERTY_ID"
        ) AS next_adjuster_id,

        LEAD("PAYOUT_AUTHORIZED") OVER (
            PARTITION BY "MANAGER_ID"
            ORDER BY "INCIDENT_DATE", "PROPERTY_ID"
        ) AS next_payout_authorized

    FROM reit_portfolio
)

SELECT *
FROM claim_sequence
WHERE "ADJUSTER_ID" = next_adjuster_id
ORDER BY
    "MANAGER_ID",
    "INCIDENT_DATE",
    "PROPERTY_ID";


-- ============================================================
-- TASK 7
-- Valuation tiers
-- Business logic:
-- Segments properties according to their USD valuation.
-- ============================================================

SELECT
    "PROPERTY_ID",
    "VALUATION_USD",
    CASE
        WHEN CAST("VALUATION_USD" AS NUMERIC) > 10000000
            THEN 'Tier 1'
        WHEN CAST("VALUATION_USD" AS NUMERIC) >= 1000000
            THEN 'Tier 2'
        ELSE 'Tier 3'
    END AS valuation_tier
FROM reit_portfolio;


-- ============================================================
-- TASK 8
-- Payout-to-value ratio by valuation tier
-- Business logic:
-- Determines whether lower- or higher-value properties have
-- disproportionately large insurance payouts.
-- ============================================================

WITH tiered AS (
    SELECT
        *,
        CASE
            WHEN CAST("VALUATION_USD" AS NUMERIC) > 10000000
                THEN 'Tier 1'
            WHEN CAST("VALUATION_USD" AS NUMERIC) >= 1000000
                THEN 'Tier 2'
            ELSE 'Tier 3'
        END AS valuation_tier
    FROM reit_portfolio
)

SELECT
    valuation_tier,
    COUNT(*) AS property_count,
    ROUND(
        AVG(CAST("PAYOUT_TO_VALUE_RATIO" AS NUMERIC)),
        6
    ) AS avg_payout_to_value_ratio,
    MAX(CAST("PAYOUT_TO_VALUE_RATIO" AS NUMERIC))
        AS max_payout_to_value_ratio
FROM tiered
GROUP BY valuation_tier
ORDER BY avg_payout_to_value_ratio DESC;


-- ============================================================
-- TASK 9
-- NTILE(10) payout deciles
-- Business logic:
-- Separates properties into ten payout groups to identify
-- concentration of unusually large claims.
-- ============================================================

WITH deciles AS (
    SELECT
        *,
        NTILE(10) OVER (
            ORDER BY CAST("PAYOUT_AUTHORIZED" AS NUMERIC)
        ) AS payout_decile
    FROM reit_portfolio
)
SELECT
    payout_decile,
    COUNT(*) AS property_count,
    MIN(CAST("PAYOUT_AUTHORIZED" AS NUMERIC)) AS min_payout,
    MAX(CAST("PAYOUT_AUTHORIZED" AS NUMERIC)) AS max_payout,
    AVG(CAST("PAYOUT_AUTHORIZED" AS NUMERIC)) AS avg_payout
FROM deciles
GROUP BY payout_decile
ORDER BY payout_decile;


-- ============================================================
-- TASK 12
-- Contractor / adjuster concentration
-- Business logic:
-- Identifies contractors receiving claims through multiple
-- adjusters, which may indicate collusive relationships.
-- ============================================================

SELECT
    "DECODED_CONTRACTOR" AS contractor,
    COUNT(DISTINCT "ADJUSTER_ID") AS distinct_adjusters,
    SUM(CAST("PAYOUT_AUTHORIZED" AS NUMERIC)) AS total_payout
FROM reit_portfolio
WHERE "DECODED_CONTRACTOR" IS NOT NULL
  AND "DECODED_CONTRACTOR" <> 'Standard_Vendor'
GROUP BY "DECODED_CONTRACTOR"
HAVING COUNT(DISTINCT "ADJUSTER_ID") > 3
ORDER BY
    distinct_adjusters DESC,
    total_payout DESC;


-- ============================================================
-- TASK 13
-- Running financial damage by country
-- Business logic:
-- Tracks cumulative financial damage within each country.
-- ============================================================

SELECT
    "COUNTRY_CODE",
    "INCIDENT_DATE",
    "PROPERTY_ID",

    SUM(
        CAST("TOTAL_FINANCIAL_DAMAGE_USD" AS NUMERIC)
    ) OVER (
        PARTITION BY "COUNTRY_CODE"
        ORDER BY "INCIDENT_DATE", "PROPERTY_ID"
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total_damage_usd

FROM reit_portfolio;


-- ============================================================
-- TASK 14
-- Rank adjusters within country
-- Business logic:
-- Identifies adjusters responsible for the largest suspicious
-- payout totals in each country.
-- ============================================================

SELECT
    "COUNTRY_CODE",
    "ADJUSTER_ID",

    SUM(
        CAST("PAYOUT_AUTHORIZED" AS NUMERIC)
    ) AS fake_payout_total,

    RANK() OVER (
        PARTITION BY "COUNTRY_CODE"
        ORDER BY
            SUM(
                CAST("PAYOUT_AUTHORIZED" AS NUMERIC)
            ) DESC
    ) AS adjuster_rank

FROM reit_portfolio

WHERE "PHANTOM_CLAIM_SUSPECT"::INTEGER = 1

GROUP BY
    "COUNTRY_CODE",
    "ADJUSTER_ID"

ORDER BY
    "COUNTRY_CODE",
    adjuster_rank;


-- ============================================================
-- TASK 15
-- First corrupt claim per manager
-- Business logic:
-- Identifies the earliest suspicious claim associated with
-- each manager.
-- ============================================================

WITH ranked_claims AS (
    SELECT
        "MANAGER_ID",
        "PROPERTY_ID",
        "INCIDENT_DATE",
        CAST("PAYOUT_AUTHORIZED" AS NUMERIC)
            AS payout_authorized,

        ROW_NUMBER() OVER (
            PARTITION BY "MANAGER_ID"
            ORDER BY "INCIDENT_DATE", "PROPERTY_ID"
        ) AS claim_number

    FROM reit_portfolio

    WHERE "PHANTOM_CLAIM_SUSPECT"::INTEGER = 1
)

SELECT
    "MANAGER_ID",
    "PROPERTY_ID",
    "INCIDENT_DATE",
    payout_authorized

FROM ranked_claims

WHERE claim_number = 1

ORDER BY "MANAGER_ID";


-- ============================================================
-- TASK 16
-- Adjuster tracker view
-- Business logic:
-- Summarizes bribes, shell-company relationships and payouts
-- associated with each adjuster.
-- ============================================================

CREATE OR REPLACE VIEW vw_adjuster_tracker AS
SELECT
    "ADJUSTER_ID" AS adjuster_id,

    SUM(
        CAST("ADJUSTER_GRATUITY" AS NUMERIC)
    ) AS total_bribes,

    COUNT(
        DISTINCT CASE
            WHEN "DECODED_CONTRACTOR" <> 'Standard_Vendor'
            THEN "DECODED_CONTRACTOR"
        END
    ) AS unique_shell_companies,

    SUM(
        CAST("PAYOUT_AUTHORIZED" AS NUMERIC)
    ) AS total_authorized_payouts

FROM reit_portfolio

GROUP BY "ADJUSTER_ID";


-- ============================================================
-- TASK 17
-- Contractor tracker view
-- Business logic:
-- Measures suspicious contractor activity, stolen payout
-- value and premium spikes.
-- ============================================================

CREATE OR REPLACE VIEW vw_contractor_tracker AS
SELECT
    "DECODED_CONTRACTOR" AS contractor,

    COUNT(*) AS total_incidents,

    SUM(
        CAST("PAYOUT_AUTHORIZED" AS NUMERIC)
    ) AS total_payout_stolen,

    AVG(
        CAST("PREMIUM_SPIKE_USD" AS NUMERIC)
    ) AS avg_premium_spike

FROM reit_portfolio

WHERE "DECODED_CONTRACTOR" IS NOT NULL
  AND "DECODED_CONTRACTOR" <> 'Standard_Vendor'

GROUP BY "DECODED_CONTRACTOR";


-- ============================================================
-- TASK 18
-- Master Power BI dataset
-- Business logic:
-- Combines property-level risk indicators, fraud rankings,
-- deciles, running totals and adjuster/contractor summaries.
-- ============================================================

-- Existing production view:
-- vw_powerbi_dataset


-- ============================================================
-- TASK 19
-- Clustered B-tree index
-- Business logic:
-- Physically organizes the table around adjuster/date access
-- patterns used in investigation queries.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_reit_adjuster_incident
ON reit_portfolio
USING BTREE ("ADJUSTER_ID", "INCIDENT_DATE");

CLUSTER reit_portfolio
USING idx_reit_adjuster_incident;


-- ============================================================
-- TASK 20
-- Manager index
-- Business logic:
-- Speeds up manager-based fraud and repeat-claim analysis.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_reit_manager
ON reit_portfolio ("MANAGER_ID");


-- ============================================================
-- TASK 21
-- Contractor index
-- Business logic:
-- Speeds up contractor-based collusion investigation.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_reit_decoded_contractor
ON reit_portfolio ("DECODED_CONTRACTOR");


-- ============================================================
-- TASK 22
-- Performance analysis
-- Business logic:
-- Measures execution cost of the Power BI Master View.
-- ============================================================

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM vw_powerbi_dataset
LIMIT 1000;


-- ============================================================
-- TASK 23
-- Optimization
-- Business logic:
-- Precomputes repeated adjuster/contractor aggregations so
-- the Master View does not repeatedly aggregate 1M rows.
-- ============================================================

-- Existing optimization objects:
-- mv_adjuster_tracker
-- mv_contractor_tracker


-- ============================================================
-- TASK 28
-- Recursive fraud graph
-- Business logic:
-- Represents Manager -> Fake Incident -> Adjuster ->
-- Shell Contractor relationships.
-- ============================================================

-- Existing exported result:
-- insurance_fraud_rings_graph.csv


-- ============================================================
-- TASK 29
-- Repeat-claim window output
-- Business logic:
-- Represents repeated manager/adjuster claim relationships.
-- ============================================================

-- Existing exported result:
-- repeat_claims.csv


-- ============================================================
-- TASK 30
-- Adjuster ranking export
-- Business logic:
-- Provides the ranked suspicious adjuster output.
-- ============================================================

-- Exported as:
-- interpol_most_wanted_adjusters.csv


-- ============================================================
-- END OF DAY 3 SQL ARCHITECTURE
-- ============================================================
"""

SQL_FILE.write_text(sql_content.strip() + "\n", encoding="utf-8")

print(f"Saved: {SQL_FILE.name}")


# ============================================================
# TASK 33
# Export database schema
# ============================================================

print("\n" + "=" * 70)
print("TASK 33 — DATABASE SCHEMA DDL")
print("=" * 70)

env = os.environ.copy()
env["PGPASSWORD"] = DB_PASSWORD

schema_command = [
    PG_DUMP,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-d", DB_NAME,
    "--schema-only",
    "--no-owner",
    "--no-privileges"
]

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    result = subprocess.run(
        schema_command,
        stdout=f,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

if result.returncode != 0:
    print("Schema export failed:")
    print(result.stderr)
    raise SystemExit(1)

print(f"Schema saved: {SCHEMA_FILE.name}")


# ============================================================
# TASK 34
# VACUUM + ANALYZE
# ============================================================

print("\n" + "=" * 70)
print("TASK 34 — VACUUM AND ANALYZE")
print("=" * 70)

conn.commit()
cur.close()
conn.close()

# VACUUM cannot run inside a transaction, so use psql.
vacuum_command = [
    PSQL,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-d", DB_NAME,
    "-c", "VACUUM ANALYZE reit_portfolio;"
]

result = subprocess.run(
    vacuum_command,
    capture_output=True,
    text=True,
    env=env
)

if result.returncode != 0:
    print("VACUUM failed:")
    print(result.stderr)
    raise SystemExit(1)

print(result.stdout)
print("VACUUM ANALYZE completed.")


# ============================================================
# TASK 35
# PostgreSQL backup
# ============================================================

print("\n" + "=" * 70)
print("TASK 35 — DATABASE BACKUP")
print("=" * 70)

backup_command = [
    PG_DUMP,
    "-U", DB_USER,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-d", DB_NAME,
    "-Fc",
    "-f", str(BACKUP_FILE)
]

result = subprocess.run(
    backup_command,
    capture_output=True,
    text=True,
    env=env
)

if result.returncode != 0:
    print("Database backup failed:")
    print(result.stderr)
    raise SystemExit(1)

print(f"Backup created: {BACKUP_FILE.name}")
print(
    f"Backup size: "
    f"{BACKUP_FILE.stat().st_size / (1024 * 1024):.2f} MB"
)


# ============================================================
# TASK 36
# ZIP SQL scripts + backup + existing outputs
# ============================================================

print("\n" + "=" * 70)
print("TASK 36 — CREATE sql_architecture.zip")
print("=" * 70)

files_to_zip = [
    SQL_FILE,
    SCHEMA_FILE,
    BACKUP_FILE,
    PROJECT_DIR / "powerbi_ready.csv",
    PROJECT_DIR / "repeat_claims.csv",
    PROJECT_DIR / "insurance_fraud_rings_graph.csv",
    rank_csv,
]

with zipfile.ZipFile(
    ZIP_FILE,
    "w",
    compression=zipfile.ZIP_DEFLATED
) as zipf:

    for file_path in files_to_zip:
        if file_path.exists():
            zipf.write(
                file_path,
                arcname=file_path.name
            )
            print(f"Added: {file_path.name}")
        else:
            print(f"Skipped missing file: {file_path.name}")


# ============================================================
# FINAL VERIFICATION
# ============================================================

print("\n" + "=" * 70)
print("DAY 3 TASKS 28–36 — FINAL VERIFICATION")
print("=" * 70)

outputs = [
    "repeat_claims.csv",
    "insurance_fraud_rings_graph.csv",
    "interpol_most_wanted_adjusters.csv",
    "insurance_fraud_queries.sql",
    "insurance_schema.sql",
    "powerbi_ready.csv",
    "nexlyra_insurance_backup.bak",
    "sql_architecture.zip",
]

for filename in outputs:
    path = PROJECT_DIR / filename

    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"[OK] {filename:<45} {size_mb:>10.2f} MB")
    else:
        print(f"[MISSING] {filename}")

print("\n" + "=" * 70)
print("DAY 3 FINAL BATCH COMPLETE")
print("=" * 70)
