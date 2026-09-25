# Nexlyra Insurance Fraud & Premium Embezzlement Audit

## Executive summary
This project applies forensic analytics to a one-million-record insurance portfolio. The verified workflow flags **60 records** under the project-defined `PHANTOM_CLAIM_SUSPECT` rule, representing **$433.38M in authorized payouts** and **$492.71M in combined payout and premium-spike financial damage**.

The results are investigative screening indicators for independent claim-file review, not legal findings of misconduct.

## Tech Stack
Python (Pandas, Scikit-learn), SQL (CTEs, window functions, recursive queries), Power BI (Star Schema)

## Problem Statement
Identify claims where authorized payouts are inflated via engineered premium spikes and fabricated/duplicated disaster claims, and prioritize the managers, adjusters, and contractors most associated with the exposure.

## Verified findings

| Metric | Result |
|---|---:|
| Phantom-claim suspect records | 60 |
| Authorized payouts represented | $433.38M |
| Combined payout plus premium-spike damage | $492.71M |
| Managers with phantom-claim records | 3 |
| Isolation Forest flags | 197,167 (19.72%) |
| Benford observations | 149,698 |
| Benford mean absolute deviation | 0.06139 |
| Benford chi-square | 59,768.04 |

Top manager review targets: `MGR-299`, `MGR-144`, `MGR-288`. Adjuster evidence supports `ADJ-1333` and `ADJ-1111` as priority review targets.

## Detection workflow
- Recover malformed metadata and mixed incident dates.
- Decode Base85/Ascii85 contractor fields and normalize financial values to USD.
- Derive premium-spike and payout-to-value measures.
- Apply `PREMIUM_SPIKE_USD > 2 * BASE_PREMIUM_USD` and `PAYOUT_AUTHORIZED > $50,000`.
- Use recursive SQL relationship analysis, Benford's Law, Isolation Forest triage, Pareto prioritization, and Power BI reporting.

## Recommended controls
1. Route claims above $50,000 to enhanced review.
2. Require independent inspection before final payment when risk criteria trigger.
3. Hold material premium spikes and recurring adjuster-contractor relationships for documentary review.
4. Retain model evidence, inspections, vendor records, contracts, and payment approvals.

## Limitations
Benford deviations, model flags, relationship concentration, and payout patterns require validation against claim files. Named managers, adjusters, contractors, and properties are review candidates, not confirmed wrongdoers.

## Charts and dashboard evidence

### Benford's Law and anomaly evidence
![Benford's Law claim evidence](images/forensic_images/benfords_law_claim_proof.png)
![Multivariate anomalies](images/forensic_images/multivariate_anomalies.png)

### Payout and fraud patterns
![Payout fraud evidence](images/forensic_images/payout_fraud_proof.png)
![Extortion scaling trend](images/forensic_images/extortion_scaling_trend.png)
![Fraud seasonality](images/forensic_images/fraud_seasonality.png)

### Dashboard pages
Excel
<img width="1410" height="677" alt="image" src="https://github.com/user-attachments/assets/d5c0d797-abc9-455e-8223-f7a7e24c5a7a" />
Power BI
![Insurance dashboard page 1](images/dashboard_screenshots/dashboard_page_1.png)

## Repository contents
Data engineering scripts, SQL architecture, processed and forensic outputs, dashboard assets, images, and supporting insurance audit reports.
