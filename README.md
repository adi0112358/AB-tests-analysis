# A/B Test Analysis

An end-to-end data analyst project focused on evaluating whether a product change improved business performance. This project simulates a realistic signup-to-purchase experiment, measures treatment impact across key funnel metrics, and translates statistical results into business recommendations.

## Business Goal

Determine whether a new product experience should be rolled out by answering three common analyst questions:

1. Did the treatment improve conversion?
2. Did the treatment improve downstream revenue and engagement quality?
3. Which user segments responded best or worst to the experiment?

## What This Project Demonstrates

- Experiment design thinking and metric definition
- SQL-based experiment analysis in SQLite
- Python-based uplift and significance analysis
- Segment-level performance interpretation
- Stakeholder-ready reporting and dashboarding

## Tech Stack

- Python
- SQL (SQLite)
- pandas
- numpy
- Streamlit
- Plotly

## Project Layout

```text
ab-test-analysis/
  dashboard/
  data/
    raw/
    processed/
  reports/
  scripts/
  sql/
  README.md
  requirements.txt
```

## Experiment Scenario

The experiment compares:

- `control`: existing checkout and onboarding flow
- `treatment`: redesigned flow with clearer messaging and simplified steps

The simulated data includes:

- user assignment
- device type
- traffic source
- landing page variant
- signup conversion
- purchase conversion
- revenue per user
- session engagement

## Quick Start

```bash
cd /Users/aditya/Desktop/DA/ab-test-analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/generate_experiment_data.py
python3 scripts/build_experiment_assets.py
streamlit run dashboard/app.py
```

## Key Outputs

- `data/raw/experiment_events.csv`: source experiment dataset
- `data/processed/ab_test_analysis.db`: SQLite database
- `data/processed/*.csv`: summarized KPI and segment tables
- `reports/experiment_summary.md`: stakeholder-facing findings

