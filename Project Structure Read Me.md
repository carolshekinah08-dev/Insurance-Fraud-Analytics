# Nexlyra REIT: Phantom Disaster Claims & Premium Embezzlement Audit

## Executive overview

This project examines insurance-claim and premium-spike risk in Nexlyra REIT's global property portfolio. The analysis is an investigative risk assessment: flagged claims and linked entities are indicators for independent review, not legal findings of misconduct.

The verified Day 6 metrics identify 60 records that meet the project-defined `PHANTOM_CLAIM_SUSPECT` rule. Those records represent $433.38M in authorized payouts and $492.71M in combined payout and premium-spike financial damage.

## Project structure

```text
Project 2/
├── dashboards/                  # Excel audit, Power BI report, and PDF exports
├── data/
│   ├── database/                # PostgreSQL backup
│   ├── forensic_outputs/        # Verified CSV, JSON, graph, and diagnostic outputs
│   ├── processed/               # Audit subset and partitioned Parquet dataset
│   └── raw/                     # Original 1M-row CSV
├── images/forensic_images/      # Chart evidence used in the executive report
├── reports/                     # Final Word and PDF executive report
├── scripts/                     # Data engineering and diagnostic Python scripts
└── sql/                         # Schema, forensic queries, and SQL workflow scripts
```

## Data engineering

`scripts/data_engineering.py` processes the original CSV and prepares the investigation dataset.

- Cleans mixed standard and hexadecimal-epoch incident dates.
- Uses regular expressions, rather than relying on `json.loads`, to recover values from malformed insurance metadata.
- Extracts incident classification, authorized payout, contractor token, and adjuster gratuity.
- Decodes the Base85/Ascii85 contractor field with `base64.a85decode` to reveal the contractor label used for analysis.
- Converts local currency values to USD, derives premium-spike, payout-to-value, kickback, and total-financial-damage fields, and flags claims where `PREMIUM_SPIKE_USD > 2 × BASE_PREMIUM_USD` and `PAYOUT_AUTHORIZED > $50,000`.
- Writes the cleaned portfolio as country-partitioned Parquet and exports the flagged audit subset.

## Analytical architecture

### Star schema

The Power BI-ready dataset is a property-claim fact table at the center of the model. It is joined or sliced through dimensions such as property, manager, adjuster, contractor, incident date, country, property type, and valuation tier. The fact table includes claim value, premium movement, gratuity, fraud indicators, payout-to-value ratio, and total financial damage. This supports consistent aggregation in Power BI while retaining property-level drill-through.

### Recursive SQL forensics

`sql/insurance_fraud_queries.sql` documents the SQL architecture, including window functions, ranking, materialized tracker views, and the recursive relationship logic. The exported graph in `data/forensic_outputs/insurance_fraud_rings_graph.csv` represents the investigation path:

```text
Manager → flagged incident/property → adjuster → decoded contractor
```

This structure makes concentration and repeated relationships visible for review. It does not independently prove intent, wrongdoing, or a legal relationship.

## Statistical forensics

`scripts/diagnostic_analytics.py` contains the Day 4 diagnostic workflow and writes its evidence to `data/forensic_outputs/` and `images/forensic_images/`.

- **Benford's Law:** 149,698 positive payouts were tested. The mean absolute deviation was 0.06139 and chi-square was 59,768.04. The leading-digit pattern materially departs from the logarithmic distribution expected under Benford's Law, especially for digits 1-4; this is a screening signal requiring claim-file validation.
- **Isolation Forest:** six financial and ratio features produced 197,167 model flags (19.72% of the 1M observations). The model should be operationalized as a triage queue, with investigators validating evidence before any adverse action.
- **Pareto concentration:** only three managers have records that meet the project-defined phantom-claim rule. Their flagged financial damage is concentrated in MGR-299, MGR-144, and MGR-288.

## Installation and use

1. Install Python 3.11 or later and PostgreSQL if you intend to reproduce the database steps.
2. From the project root, create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r scripts\requirements.txt
   ```

3. Set credentials only in your environment; do not place passwords in source files:

   ```powershell
   $env:NEXLYRA_DB_PASSWORD = "<your-postgresql-password>"
   $env:NEXLYRA_PSQL = "psql"
   $env:NEXLYRA_PG_DUMP = "pg_dump"
   ```

4. Run the workflows from the project root:

   ```powershell
   python scripts\data_engineering.py
   python sql\day3_final.py
   python sql\day3_powerbi.py
   python scripts\diagnostic_analytics.py
   ```

Running the full pipeline regenerates large artifacts. The supplied outputs are preserved in `data/`, so rerun only when you intend to reproduce the analysis.

## Dashboard and report

- Power BI report: `dashboards/Nexlyra_InsuranceFraud_Dashboard.pbix`
- Excel audit workbook: `dashboards/Nexlyra_Insurance_Audit_Final.xlsx`
- Executive report: `reports/Nexlyra_Executive_InsuranceFraud_Report.pdf`

## Controls recommended by the audit

1. Require independent, third-party inspection before authorizing any claim above $50,000.
2. Hold claims with a material premium-spike or a recurring adjuster-contractor relationship for documentary review.
3. Run Isolation Forest monitoring continuously and route model flags to a human review queue with retained evidence and disposition records.

## Evidence limits

The outputs identify statistical anomalies and operational risk indicators. They should be corroborated through claim files, site inspections, vendor records, insurer communication, and legal/compliance review before cancellation, recovery, disciplinary action, or external reporting.

##  Executive Deliverables

- `Nexlyra_Executive_InsuranceFraud_Report.docx` — executive Word report.
- `Nexlyra_Executive_InsuranceFraud_Report.pdf` — final executive PDF.
- `CRO_Email_Template.txt` — delivery email template.

### Verified forensic metrics

- 60 records meet the project-defined `PHANTOM_CLAIM_SUSPECT` rule.
- $433.38M in authorized payouts are represented by those records.
- $492.71M is the reported combined payout and premium-spike financial damage.
- Pareto analysis identifies three managers with phantom-claim records: `MGR-299`, `MGR-144`, and `MGR-288`.
- Benford analysis tested 149,698 positive payouts; mean absolute deviation was 0.06139 and chi-square was 59,768.04.
- Isolation Forest produced 197,167 model flags (19.72% of 1M observations).


### Interpretation

Statistical anomalies and relationship patterns are screening indicators. They must be corroborated with claim files, site inspections, vendor records, insurer communication, and legal/compliance review before cancellation, recovery, disciplinary action, or external reporting.
