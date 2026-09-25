
"""
Day 4 — Diagnostic Analytics & Statistical Forensics
Nexlyra Insurance Fraud Investigation

Tasks covered: 1–36 in one batch.

Input:
    powerbi_ready.csv

Outputs:
    payout_fraud_proof.png
    benfords_law_claim_proof.png
    extortion_scaling_trend.png
    fraud_seasonality.png
    smoothed_extortion_trend.png
    multivariate_anomalies.png
    property_type_variance.png
    insurance_theft_summary_stats.csv
    rogue_property_managers.csv
    multidimensional_fraud.csv
    insurance_fraud_insights.json
    forensic_images/
    forensic_images.zip
    day4_sweetviz_report.html
    requirements.txt
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from scipy import stats
from sklearn.ensemble import IsolationForest

try:
    import sweetviz as sv
except ImportError:
    sv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = PROJECT_ROOT / "data" / "forensic_outputs"
INPUT_FILE = BASE_DIR / "powerbi_ready.csv"
FORENSIC_DIR = PROJECT_ROOT / "images" / "forensic_images"
BASE_DIR.mkdir(parents=True, exist_ok=True)
FORENSIC_DIR.mkdir(parents=True, exist_ok=True)

# Nexlyra-inspired palette based on the logo supplied for this project.
NEXLYRA_COLORS: dict[str, str] = {
    "navy": "#071426",
    "dark_blue": "#123B73",
    "blue": "#1E5DB7",
    "bright_blue": "#1689E8",
    "cyan": "#20BCEB",
    "silver": "#AEB7C4",
    "white": "#FFFFFF",
    "danger": "#D64545",
}

console = Console()


def banner(title: str) -> None:
    """Print a consistent Rich section banner."""
    console.print()
    console.print(
        Panel(
            f"[bold]{title}[/bold]",
            border_style=NEXLYRA_COLORS["bright_blue"],
        )
    )


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    """Convert a dataframe column to numeric values, coercing invalid values to NaN."""
    return pd.to_numeric(df[column], errors="coerce")


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Convert financial/date fields to analysis-friendly numeric and datetime types."""
    numeric_columns = [
        "PAYOUT_AUTHORIZED",
        "VALUATION_USD",
        "CURRENT_PREMIUM_USD",
        "PREMIUM_SPIKE_USD",
        "ADJUSTER_GRATUITY",
        "TOTAL_FINANCIAL_DAMAGE_USD",
        "PAYOUT_TO_VALUE_RATIO",
        "ADJUSTER_KICKBACK_RATIO",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "INCIDENT_DATE" in df.columns:
        df["INCIDENT_DATE"] = pd.to_datetime(
            df["INCIDENT_DATE"], errors="coerce"
        )

    return df


def configure_plotting() -> None:
    """Configure Seaborn and Matplotlib using the Nexlyra-inspired palette."""
    sns.set_theme(style="whitegrid")
    sns.set_palette(
        [
            NEXLYRA_COLORS["navy"],
            NEXLYRA_COLORS["dark_blue"],
            NEXLYRA_COLORS["blue"],
            NEXLYRA_COLORS["bright_blue"],
            NEXLYRA_COLORS["cyan"],
            NEXLYRA_COLORS["silver"],
        ]
    )
    plt.rcParams["figure.figsize"] = (11, 6)
    plt.rcParams["axes.titleweight"] = "bold"


def save_chart(fig: plt.Figure, filename: str) -> None:
    """Save a chart in the project folder and close the figure."""
    path = BASE_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def load_dataset() -> pd.DataFrame:
    """Load powerbi_ready.csv and prepare its analysis columns."""
    banner("TASKS 1–2 — LOAD POWER BI DATASET")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    console.print(f"Loading: {INPUT_FILE.name}")
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    console.print(f"[green]Rows:[/green] {len(df):,}")
    console.print(f"[green]Columns:[/green] {len(df.columns):,}")

    return prepare_data(df)


def independent_t_test(df: pd.DataFrame) -> dict[str, Any]:
    """Compare Apex Restoration and Global Rebuild payout distributions."""
    banner("TASKS 3–5 — INDEPENDENT TWO-SAMPLE T-TEST")

    # The supplied task wording is truncated after “claims paid t...”.
    # We use Global Rebuild as the comparison cohort.
    apex = df.loc[
        df["DECODED_CONTRACTOR"].eq("Apex Restoration"),
        "PAYOUT_AUTHORIZED",
    ].dropna()

    comparison = df.loc[
        df["DECODED_CONTRACTOR"].eq("Global Rebuild"),
        "PAYOUT_AUTHORIZED",
    ].dropna()

    if len(apex) < 2 or len(comparison) < 2:
        raise ValueError("Insufficient observations for the two-sample t-test.")

    t_stat, p_value = stats.ttest_ind(apex, comparison, equal_var=False)

    # H0: mean Apex payout <= mean Global Rebuild payout.
    # H1: mean Apex payout > mean Global Rebuild payout.
    one_sided_p = p_value / 2 if t_stat > 0 else 1 - (p_value / 2)

    result: dict[str, Any] = {
        "null_hypothesis": (
            "H0: Mean payout for Apex Restoration is less than or equal "
            "to mean payout for Global Rebuild."
        ),
        "alternative_hypothesis": (
            "H1: Mean payout for Apex Restoration is greater than "
            "mean payout for Global Rebuild."
        ),
        "apex_count": int(len(apex)),
        "global_rebuild_count": int(len(comparison)),
        "apex_mean": float(apex.mean()),
        "global_rebuild_mean": float(comparison.mean()),
        "t_statistic": float(t_stat),
        "two_sided_p_value": float(p_value),
        "one_sided_p_value": float(one_sided_p),
        "significant_at_0_05": bool(one_sided_p < 0.05),
    }

    console.print(f"Apex mean: ${apex.mean():,.2f}")
    console.print(f"Global Rebuild mean: ${comparison.mean():,.2f}")
    console.print(f"T-statistic: {t_stat:,.6f}")
    console.print(f"One-sided p-value: {one_sided_p:.12g}")

    banner("TASK 6 — PAYOUT FRAUD PROOF BOXPLOT")

    plot_df = df[
        df["DECODED_CONTRACTOR"].isin(
            ["Apex Restoration", "Global Rebuild"]
        )
    ][["DECODED_CONTRACTOR", "PAYOUT_AUTHORIZED"]].dropna()

    fig, ax = plt.subplots()
    sns.boxplot(
        data=plot_df,
        x="DECODED_CONTRACTOR",
        y="PAYOUT_AUTHORIZED",
        ax=ax,
    )
    ax.set_title("Payout Discrepancy: Apex Restoration vs Global Rebuild")
    ax.set_xlabel("Contractor")
    ax.set_ylabel("Authorized Payout (USD)")
    save_chart(fig, "payout_fraud_proof.png")

    return result


def benford_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Apply Benford's Law to positive authorized payout values."""
    banner("TASKS 7–9 — BENFORD'S LAW")

    values = df["PAYOUT_AUTHORIZED"].dropna()
    values = values[values > 0]

    first_digits = (
        values.astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.lstrip("0")
        .str[0]
    )
    first_digits = first_digits[first_digits.isin(list("123456789"))]

    actual_counts = first_digits.value_counts().reindex(
        list("123456789"), fill_value=0
    )
    actual_freq = actual_counts / actual_counts.sum()

    digits = np.arange(1, 10)
    expected_freq = np.log10(1 + 1 / digits)

    # Chi-square goodness-of-fit against Benford expected frequencies.
    observed_counts = actual_freq.values * actual_counts.sum()
    expected_counts = expected_freq * actual_counts.sum()
    chi2, chi_p = stats.chisquare(
        f_obs=observed_counts,
        f_exp=expected_counts,
    )

    deviations = actual_freq.values - expected_freq

    result: dict[str, Any] = {
        "observations": int(actual_counts.sum()),
        "actual_leading_digit_frequencies": {
            str(d): float(f) for d, f in zip(digits, actual_freq)
        },
        "benford_expected_frequencies": {
            str(d): float(f) for d, f in zip(digits, expected_freq)
        },
        "absolute_deviation_by_digit": {
            str(d): float(abs(dev))
            for d, dev in zip(digits, deviations)
        },
        "mean_absolute_deviation": float(np.mean(np.abs(deviations))),
        "chi_square": float(chi2),
        "chi_square_p_value": float(chi_p),
    }

    console.print(f"Observations: {actual_counts.sum():,}")
    console.print(f"Chi-square: {chi2:,.4f}")
    console.print(f"p-value: {chi_p:.12g}")

    fig, ax = plt.subplots()
    x = np.arange(1, 10)
    width = 0.38

    ax.bar(
        x - width / 2,
        actual_freq.values,
        width=width,
        label="Actual",
        color=NEXLYRA_COLORS["blue"],
    )
    ax.bar(
        x + width / 2,
        expected_freq,
        width=width,
        label="Benford Expected",
        color=NEXLYRA_COLORS["cyan"],
    )
    ax.set_xticks(x)
    ax.set_xlabel("Leading Digit")
    ax.set_ylabel("Frequency")
    ax.set_title("Benford's Law: Actual vs Expected Leading Digits")
    ax.legend()

    save_chart(fig, "benfords_law_claim_proof.png")

    return result


def correlation_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate Pearson and Spearman correlations for valuation and payout."""
    banner("TASKS 10–12 — CORRELATION & EXTORTION SCALING")

    clean = df[["VALUATION_USD", "PAYOUT_AUTHORIZED"]].dropna()

    pearson_r, pearson_p = stats.pearsonr(
        clean["VALUATION_USD"],
        clean["PAYOUT_AUTHORIZED"],
    )
    spearman_r, spearman_p = stats.spearmanr(
        clean["VALUATION_USD"],
        clean["PAYOUT_AUTHORIZED"],
    )

    console.print(f"Pearson r: {pearson_r:.6f}")
    console.print(f"Pearson p-value: {pearson_p:.12g}")
    console.print(f"Spearman rho: {spearman_r:.6f}")
    console.print(f"Spearman p-value: {spearman_p:.12g}")

    # Plot a bounded sample so a million-point scatter does not create a
    # massive image or unnecessarily consume memory.
    plot_sample = clean.sample(
        n=min(100_000, len(clean)),
        random_state=42,
    )

    fig, ax = plt.subplots()
    sns.regplot(
        data=plot_sample,
        x="VALUATION_USD",
        y="PAYOUT_AUTHORIZED",
        scatter_kws={"s": 8, "alpha": 0.25},
        line_kws={"linewidth": 2},
        ax=ax,
    )
    ax.set_title("Valuation vs Authorized Payout")
    ax.set_xlabel("Valuation (USD)")
    ax.set_ylabel("Authorized Payout (USD)")
    save_chart(fig, "extortion_scaling_trend.png")

    return {
        "pearson_r": float(pearson_r),
        "pearson_p_value": float(pearson_p),
        "spearman_rho": float(spearman_r),
        "spearman_p_value": float(spearman_p),
        "observations": int(len(clean)),
    }


def pareto_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Identify managers contributing to the top 20 percent of financial damage."""
    banner("TASK 13 — PARETO ANALYSIS")

    manager_damage = (
        df.groupby("MANAGER_ID", dropna=False)["TOTAL_FINANCIAL_DAMAGE_USD"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"TOTAL_FINANCIAL_DAMAGE_USD": "total_damage_usd"})
    )

    manager_damage["cumulative_damage"] = (
        manager_damage["total_damage_usd"].cumsum()
    )
    total_damage = manager_damage["total_damage_usd"].sum()

    if total_damage != 0:
        manager_damage["cumulative_share"] = (
            manager_damage["cumulative_damage"] / total_damage
        )
    else:
        manager_damage["cumulative_share"] = 0.0

    top_20_count = max(1, math.ceil(len(manager_damage) * 0.20))
    pareto_managers = manager_damage.head(top_20_count).copy()

    pareto_managers.to_csv(
        BASE_DIR / "rogue_property_managers.csv",
        index=False,
    )

    console.print(
        f"Managers analyzed: {len(manager_damage):,}; "
        f"top 20% count: {top_20_count:,}"
    )
    console.print(
        f"Top 20% managers' damage share: "
        f"{pareto_managers['total_damage_usd'].sum() / total_damage:.2%}"
        if total_damage
        else "Damage share unavailable."
    )

    return pareto_managers


def premium_mad(df: pd.DataFrame) -> float:
    """Calculate mean absolute deviation for current premium in USD."""
    banner("TASK 14 — MEAN ABSOLUTE DEVIATION")

    values = df["CURRENT_PREMIUM_USD"].dropna()
    mad = float(np.mean(np.abs(values - values.mean())))

    console.print(f"Current Premium MAD: ${mad:,.6f}")
    return mad


def time_series_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze monthly gratuity and create a 30-day premium-spike trend."""
    banner("TASKS 15–16 — SEASONALITY & SMOOTHED EXTORTION TREND")

    dated = df.dropna(subset=["INCIDENT_DATE"]).copy()

    monthly = (
        dated.assign(month=dated["INCIDENT_DATE"].dt.to_period("M").dt.to_timestamp())
        .groupby("month")["ADJUSTER_GRATUITY"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots()
    ax.plot(
        monthly["month"],
        monthly["ADJUSTER_GRATUITY"],
        linewidth=2,
    )
    ax.set_title("Average Adjuster Gratuity by Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average Adjuster Gratuity (USD)")
    fig.autofmt_xdate()
    save_chart(fig, "fraud_seasonality.png")

    daily = (
        dated.groupby("INCIDENT_DATE")["PREMIUM_SPIKE_USD"]
        .mean()
        .sort_index()
    )
    rolling = daily.rolling("30D").mean()

    fig, ax = plt.subplots()
    ax.plot(
        daily.index,
        rolling.values,
        linewidth=2,
    )
    ax.set_title("30-Day Rolling Average of Premium Spikes")
    ax.set_xlabel("Incident Date")
    ax.set_ylabel("Rolling Average Premium Spike (USD)")
    fig.autofmt_xdate()
    save_chart(fig, "smoothed_extortion_trend.png")

    return {
        "monthly_rows": int(len(monthly)),
        "daily_rows": int(len(daily)),
    }


def isolation_forest(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Detect multidimensional financial anomalies using Isolation Forest."""
    banner("TASKS 17–21 — ISOLATION FOREST ANOMALY DETECTION")

    feature_columns = [
        "PAYOUT_AUTHORIZED",
        "PREMIUM_SPIKE_USD",
        "ADJUSTER_GRATUITY",
        "TOTAL_FINANCIAL_DAMAGE_USD",
        "PAYOUT_TO_VALUE_RATIO",
        "VALUATION_USD",
    ]

    features = df[feature_columns].copy()

    # Fill missing values using medians so the estimator receives a complete matrix.
    features = features.replace([np.inf, -np.inf], np.nan)
    features = features.fillna(features.median(numeric_only=True))

    model = IsolationForest(
        n_estimators=150,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(features)
    df["isolation_forest_flag"] = model.predict(features)
    df["isolation_forest_score"] = model.decision_function(features)

    anomalies = df[df["isolation_forest_flag"].eq(-1)].copy()

    output_columns = [
        "PROPERTY_ID",
        "INCIDENT_DATE",
        "MANAGER_ID",
        "ADJUSTER_ID",
        "COUNTRY_CODE",
        "PROPERTY_TYPE",
        "DECODED_CONTRACTOR",
        "PAYOUT_AUTHORIZED",
        "PREMIUM_SPIKE_USD",
        "ADJUSTER_GRATUITY",
        "TOTAL_FINANCIAL_DAMAGE_USD",
        "PAYOUT_TO_VALUE_RATIO",
        "VALUATION_USD",
        "isolation_forest_score",
    ]
    output_columns = [c for c in output_columns if c in anomalies.columns]

    anomalies[output_columns].to_csv(
        BASE_DIR / "multidimensional_fraud.csv",
        index=False,
    )

    country_counts = (
        anomalies["COUNTRY_CODE"]
        .value_counts(dropna=False)
        .sort_values(ascending=False)
    )

    console.print(f"Anomalies detected: {len(anomalies):,}")
    console.print("Outliers by country:")
    for country, count in country_counts.items():
        console.print(f"  {country}: {count:,}")

    fig, ax = plt.subplots()
    country_counts.plot(
        kind="bar",
        ax=ax,
        color=NEXLYRA_COLORS["bright_blue"],
    )
    ax.set_title("Isolation Forest Outliers by Country")
    ax.set_xlabel("Country Code")
    ax.set_ylabel("Number of Outliers")
    save_chart(fig, "multivariate_anomalies.png")

    return anomalies, {
        "feature_columns": feature_columns,
        "anomaly_count": int(len(anomalies)),
        "anomaly_rate": float(len(anomalies) / len(df)),
        "country_counts": {
            str(k): int(v) for k, v in country_counts.items()
        },
    }


def property_type_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Compare payout distributions across property types."""
    banner("TASKS 22–23 — PROPERTY TYPE VARIANCE")

    grouped = (
        df.groupby("PROPERTY_TYPE")["PAYOUT_AUTHORIZED"]
        .agg(["count", "mean", "median", "std", "sum"])
        .sort_values("sum", ascending=False)
    )

    console.print(grouped.to_string())

    fig, ax = plt.subplots(figsize=(12, 7))
    plot_df = df[
        ["PROPERTY_TYPE", "PAYOUT_AUTHORIZED"]
    ].dropna()

    # A sample keeps the violin plot practical with one million records.
    plot_df = plot_df.sample(
        n=min(150_000, len(plot_df)),
        random_state=42,
    )

    sns.violinplot(
        data=plot_df,
        x="PROPERTY_TYPE",
        y="PAYOUT_AUTHORIZED",
        cut=0,
        ax=ax,
    )
    ax.set_title("Payout Distribution by Property Type")
    ax.set_xlabel("Property Type")
    ax.set_ylabel("Authorized Payout (USD)")
    ax.tick_params(axis="x", rotation=25)
    save_chart(fig, "property_type_variance.png")

    return {
        str(k): {
            str(stat): float(value) if pd.notna(value) else None
            for stat, value in row.items()
        }
        for k, row in grouped.iterrows()
    }


def descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate descriptive statistics for authorized claim payouts."""
    banner("TASKS 24–25 — DESCRIPTIVE STATISTICS")

    payout = df["PAYOUT_AUTHORIZED"].dropna()

    summary = pd.DataFrame(
        {
            "mean": [payout.mean()],
            "median": [payout.median()],
            "std": [payout.std()],
            "min": [payout.min()],
            "max": [payout.max()],
            "count": [len(payout)],
        }
    )

    summary.to_csv(
        BASE_DIR / "insurance_theft_summary_stats.csv",
        index=False,
    )

    console.print(summary.to_string(index=False))
    return summary


def print_diagnostic_report(
    ttest_result: dict[str, Any],
    benford_result: dict[str, Any],
    correlation_result: dict[str, Any],
    anomalies_result: dict[str, Any],
) -> None:
    """Print the principal Day 4 findings using Rich formatting."""
    banner("TASKS 26–27 — FORMATTED DIAGNOSTIC REPORT")

    table = Table(title="Nexlyra Insurance Diagnostic Findings")

    table.add_column("Analysis")
    table.add_column("Finding")
    table.add_column("Result")

    table.add_row(
        "T-Test",
        "Apex vs Global Rebuild",
        f"p = {ttest_result['one_sided_p_value']:.6g}",
    )
    table.add_row(
        "Benford",
        "Chi-square goodness-of-fit",
        f"p = {benford_result['chi_square_p_value']:.6g}",
    )
    table.add_row(
        "Pearson",
        "Valuation vs Payout",
        f"r = {correlation_result['pearson_r']:.6f}",
    )
    table.add_row(
        "Spearman",
        "Valuation vs Payout",
        f"rho = {correlation_result['spearman_rho']:.6f}",
    )
    table.add_row(
        "Isolation Forest",
        "Multivariate anomalies",
        f"{anomalies_result['anomaly_count']:,}",
    )

    console.print(table)


def create_insights_json(
    ttest_result: dict[str, Any],
    benford_result: dict[str, Any],
    correlation_result: dict[str, Any],
    pareto_managers: pd.DataFrame,
    mad: float,
    seasonality_result: dict[str, Any],
    anomalies_result: dict[str, Any],
    property_result: dict[str, Any],
    summary: pd.DataFrame,
) -> None:
    """Save statistical findings, p-values and forensic outputs to JSON."""
    banner("TASK 34 — SAVE INSURANCE FRAUD INSIGHTS JSON")

    payload: dict[str, Any] = {
        "python_version": sys.version,
        "t_test": ttest_result,
        "benfords_law": benford_result,
        "correlations": correlation_result,
        "pareto": {
            "manager_count": int(len(pareto_managers)),
            "managers": pareto_managers[
                ["MANAGER_ID", "total_damage_usd", "cumulative_share"]
            ].to_dict(orient="records"),
        },
        "premium_mad": mad,
        "seasonality": seasonality_result,
        "isolation_forest": anomalies_result,
        "property_type_analysis": property_result,
        "claim_payout_descriptive_statistics": {
            str(k): float(v)
            for k, v in summary.iloc[0].items()
        },
    }

    with open(
        BASE_DIR / "insurance_fraud_insights.json",
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(payload, handle, indent=2, default=str)

    console.print("Saved: insurance_fraud_insights.json")


def create_forensic_package() -> None:
    """Copy generated PNG charts into forensic_images and create a ZIP archive."""
    banner("TASK 33 — FORENSIC IMAGES PACKAGE")

    FORENSIC_DIR.mkdir(exist_ok=True)

    chart_names = [
        "payout_fraud_proof.png",
        "benfords_law_claim_proof.png",
        "extortion_scaling_trend.png",
        "fraud_seasonality.png",
        "smoothed_extortion_trend.png",
        "multivariate_anomalies.png",
        "property_type_variance.png",
    ]

    for name in chart_names:
        source = BASE_DIR / name
        if source.exists():
            shutil.copy2(source, FORENSIC_DIR / name)
            console.print(f"Added: {name}")

    archive_base = BASE_DIR / "forensic_images"
    shutil.make_archive(
        str(archive_base),
        "zip",
        root_dir=FORENSIC_DIR,
    )

    console.print("Created: forensic_images.zip")


def create_sweetviz_report(df: pd.DataFrame) -> None:
    """Generate a Sweetviz HTML report using a bounded sample of the million-row dataset."""
    banner("TASK 35 — SWEETVIZ HTML REPORT")

    if sv is None:
        console.print(
            "[yellow]Sweetviz is unavailable; skipping HTML report.[/yellow]"
        )
        return

    # A representative sample prevents a million-row profiling job from
    # becoming unnecessarily slow or producing an enormous HTML file.
    sample_size = min(50_000, len(df))
    report_df = df.sample(n=sample_size, random_state=42).copy()

    # Drop very large JSON/text fields from the report.
    drop_columns = [
        "INSURANCE_METADATA_JSON",
        "CONTRACTOR_A85",
    ]
    report_df = report_df.drop(
        columns=[c for c in drop_columns if c in report_df.columns]
    )

    report = sv.analyze(report_df)
    report.show_html(
        filepath=str(BASE_DIR / "day4_sweetviz_report.html"),
        open_browser=False,
        layout="widescreen",
    )

    console.print(
        f"Sweetviz report created from representative sample of "
        f"{sample_size:,} rows."
    )


def create_requirements() -> None:
    """Write the exact installed library versions relevant to Day 4."""
    banner("TASK 36 — REQUIREMENTS.TXT")

    import matplotlib
    import rich
    import scipy
    import seaborn
    import sklearn
    import sweetviz

    versions = [
        f"pandas=={pd.__version__}",
        f"numpy=={np.__version__}",
        f"scipy=={scipy.__version__}",
        f"matplotlib=={matplotlib.__version__}",
        f"seaborn=={seaborn.__version__}",
        f"scikit-learn=={sklearn.__version__}",
        f"rich=={rich.__version__}",
        f"sweetviz=={sweetviz.__version__}",
    ]

    (BASE_DIR / "requirements.txt").write_text(
        "\n".join(versions) + "\n",
        encoding="utf-8",
    )

    console.print("\n".join(versions))


def verify_outputs() -> None:
    """Verify that the major Day 4 output files were created."""
    banner("DAY 4 — FINAL OUTPUT VERIFICATION")

    expected = [
        "payout_fraud_proof.png",
        "benfords_law_claim_proof.png",
        "extortion_scaling_trend.png",
        "fraud_seasonality.png",
        "smoothed_extortion_trend.png",
        "multivariate_anomalies.png",
        "property_type_variance.png",
        "insurance_theft_summary_stats.csv",
        "rogue_property_managers.csv",
        "multidimensional_fraud.csv",
        "insurance_fraud_insights.json",
        "forensic_images.zip",
        "day4_sweetviz_report.html",
        "requirements.txt",
    ]

    for name in expected:
        path = BASE_DIR / name
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            console.print(f"[green][OK][/green] {name:<42} {size_mb:,.2f} MB")
        else:
            console.print(f"[red][MISSING][/red] {name}")


def main() -> None:
    """Run all Day 4 diagnostic analytics tasks in one batch."""
    configure_plotting()

    df = load_dataset()

    ttest_result = independent_t_test(df)
    benford_result = benford_analysis(df)
    correlation_result = correlation_analysis(df)
    pareto_managers = pareto_analysis(df)
    mad = premium_mad(df)
    seasonality_result = time_series_analysis(df)
    _, anomalies_result = isolation_forest(df)
    property_result = property_type_analysis(df)
    summary = descriptive_statistics(df)

    print_diagnostic_report(
        ttest_result,
        benford_result,
        correlation_result,
        anomalies_result,
    )

    create_insights_json(
        ttest_result,
        benford_result,
        correlation_result,
        pareto_managers,
        mad,
        seasonality_result,
        anomalies_result,
        property_result,
        summary,
    )

    create_forensic_package()
    create_sweetviz_report(df)
    create_requirements()
    verify_outputs()

    banner("DAY 4 TASKS 1–36 — BATCH COMPLETE")
    console.print(
        "[bold green]Diagnostic analytics pipeline completed.[/bold green]"
    )


if __name__ == "__main__":
    main()
