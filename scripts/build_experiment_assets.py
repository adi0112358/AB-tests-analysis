from __future__ import annotations

import math
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "experiment_events.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = PROCESSED_DIR / "ab_test_analysis.db"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"
REPORT_PATH = BASE_DIR / "reports" / "experiment_summary.md"


def load_source_data() -> pd.DataFrame:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing source data at {RAW_DATA_PATH}. Run scripts/generate_experiment_data.py first."
        )
    return pd.read_csv(RAW_DATA_PATH)


def write_database(df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.executescript(SCHEMA_PATH.read_text())
    df.to_sql("experiment_events", connection, if_exists="append", index=False)
    connection.close()


def _z_test(control_success: int, control_total: int, treatment_success: int, treatment_total: int) -> tuple[float, float]:
    control_rate = control_success / control_total
    treatment_rate = treatment_success / treatment_total
    pooled = (control_success + treatment_success) / (control_total + treatment_total)
    standard_error = math.sqrt(pooled * (1 - pooled) * ((1 / control_total) + (1 / treatment_total)))
    z_score = 0.0 if standard_error == 0 else (treatment_rate - control_rate) / standard_error
    cdf = 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2)))
    p_value = max(0.0, 2 * (1 - cdf))
    return z_score, p_value


def build_overall_summary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    grouped = (
        df.groupby("experiment_group", observed=False)
        .agg(
            users=("user_id", "count"),
            signup_rate_pct=("signed_up", lambda values: round(values.mean() * 100, 2)),
            purchase_rate_pct=("purchased", lambda values: round(values.mean() * 100, 2)),
            revenue_per_user=("revenue", lambda values: round(values.mean(), 2)),
            avg_session_duration_sec=("avg_session_duration_sec", lambda values: round(values.mean(), 2)),
            avg_pages_viewed=("pages_viewed", lambda values: round(values.mean(), 2)),
        )
        .reset_index()
    )

    control = df[df["experiment_group"] == "control"]
    treatment = df[df["experiment_group"] == "treatment"]

    z_score, p_value = _z_test(
        int(control["purchased"].sum()),
        len(control),
        int(treatment["purchased"].sum()),
        len(treatment),
    )

    control_purchase = control["purchased"].mean()
    treatment_purchase = treatment["purchased"].mean()
    abs_uplift = (treatment_purchase - control_purchase) * 100
    rel_uplift = 0.0 if control_purchase == 0 else ((treatment_purchase - control_purchase) / control_purchase) * 100

    experiment_result = pd.DataFrame(
        [
            {
                "control_users": len(control),
                "treatment_users": len(treatment),
                "control_purchase_rate_pct": round(control_purchase * 100, 2),
                "treatment_purchase_rate_pct": round(treatment_purchase * 100, 2),
                "absolute_uplift_pct_points": round(abs_uplift, 2),
                "relative_uplift_pct": round(rel_uplift, 2),
                "z_score": round(z_score, 3),
                "p_value": round(p_value, 5),
                "significant_at_5pct": "Yes" if p_value < 0.05 else "No",
            }
        ]
    )
    return grouped, experiment_result


def build_segment_summary(df: pd.DataFrame, column: str) -> pd.DataFrame:
    base = (
        df.groupby([column, "experiment_group"], observed=False)
        .agg(
            users=("user_id", "count"),
            purchase_rate_pct=("purchased", lambda values: round(values.mean() * 100, 2)),
            revenue_per_user=("revenue", lambda values: round(values.mean(), 2)),
            signup_rate_pct=("signed_up", lambda values: round(values.mean() * 100, 2)),
        )
        .reset_index()
    )
    pivot = base.pivot(index=column, columns="experiment_group", values="purchase_rate_pct").reset_index()
    pivot.columns.name = None
    pivot.loc[:, "purchase_rate_uplift_pct_points"] = (pivot["treatment"] - pivot["control"]).round(2)

    revenue_pivot = base.pivot(index=column, columns="experiment_group", values="revenue_per_user").reset_index()
    revenue_pivot.columns.name = None
    revenue_pivot.loc[:, "revenue_uplift"] = (revenue_pivot["treatment"] - revenue_pivot["control"]).round(2)

    merged = pivot.merge(revenue_pivot[[column, "revenue_uplift"]], on=column, how="left")
    return merged.sort_values("purchase_rate_uplift_pct_points", ascending=False)


def write_summary_files(tables: dict[str, pd.DataFrame]) -> None:
    for name, table in tables.items():
        table.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)


def write_report(overall: pd.DataFrame, result: pd.DataFrame, device_summary: pd.DataFrame, traffic_summary: pd.DataFrame) -> None:
    control = overall.loc[overall["experiment_group"] == "control"].iloc[0]
    treatment = overall.loc[overall["experiment_group"] == "treatment"].iloc[0]
    result_row = result.iloc[0]
    best_device = device_summary.iloc[0]
    weakest_source = traffic_summary.iloc[-1]

    report = f"""# A/B Test Analysis Findings

## Executive Summary

- Control users: {int(result_row["control_users"]):,}
- Treatment users: {int(result_row["treatment_users"]):,}
- Control purchase rate: {result_row["control_purchase_rate_pct"]:.2f}%
- Treatment purchase rate: {result_row["treatment_purchase_rate_pct"]:.2f}%
- Absolute uplift: {result_row["absolute_uplift_pct_points"]:.2f} percentage points
- Relative uplift: {result_row["relative_uplift_pct"]:.2f}%
- P-value: {result_row["p_value"]:.5f}
- Statistically significant at 5%: {result_row["significant_at_5pct"]}

## Key Findings

1. The treatment increased purchase conversion from **{control["purchase_rate_pct"]:.2f}%** to **{treatment["purchase_rate_pct"]:.2f}%**.
2. Revenue per user moved from **${control["revenue_per_user"]:.2f}** in control to **${treatment["revenue_per_user"]:.2f}** in treatment.
3. The strongest positive device response came from **{best_device["device_type"]}**, with a purchase-rate uplift of **{best_device["purchase_rate_uplift_pct_points"]:.2f}** points.
4. The weakest segment response came from **{weakest_source["traffic_source"]}**, with a purchase-rate uplift of **{weakest_source["purchase_rate_uplift_pct_points"]:.2f}** points.

## Recommendation

Roll out the treatment if the business prioritizes purchase conversion and revenue per user, while monitoring weaker-response segments after launch. Pair the rollout with follow-up analysis on traffic sources that underperform relative to the average treatment effect.

## How To Present This In Interviews

Explain the primary metric, show the control-versus-treatment lift, mention the significance test, and close with why segment-level analysis is critical before a full rollout decision.
"""
    REPORT_PATH.write_text(report)


def main() -> None:
    source = load_source_data()
    write_database(source)

    overall_summary, experiment_result = build_overall_summary(source)
    device_summary = build_segment_summary(source, "device_type")
    traffic_summary = build_segment_summary(source, "traffic_source")
    landing_summary = build_segment_summary(source, "landing_page")

    tables = {
        "overall_summary": overall_summary,
        "experiment_result": experiment_result,
        "device_summary": device_summary,
        "traffic_summary": traffic_summary,
        "landing_summary": landing_summary,
    }
    write_summary_files(tables)
    write_report(overall_summary, experiment_result, device_summary, traffic_summary)

    print(f"Saved SQLite database to {DB_PATH}")
    print(f"Saved {len(tables)} summary files to {PROCESSED_DIR}")
    print(f"Wrote report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
