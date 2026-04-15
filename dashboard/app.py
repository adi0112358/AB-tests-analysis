from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_PATH = BASE_DIR / "reports" / "experiment_summary.md"


@st.cache_data
def load_table(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / f"{name}.csv")


def main() -> None:
    st.set_page_config(page_title="A/B Test Analysis", layout="wide")
    st.title("A/B Test Analysis")
    st.caption("Portfolio project: evaluate experiment impact across conversion, revenue, and engagement.")

    overall = load_table("overall_summary")
    result = load_table("experiment_result").iloc[0]
    device_summary = load_table("device_summary")
    traffic_summary = load_table("traffic_summary")
    landing_summary = load_table("landing_summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Control Purchase Rate", f"{result['control_purchase_rate_pct']:.2f}%")
    col2.metric("Treatment Purchase Rate", f"{result['treatment_purchase_rate_pct']:.2f}%")
    col3.metric("Absolute Uplift", f"{result['absolute_uplift_pct_points']:.2f} pts")
    col4.metric("Significant at 5%", str(result["significant_at_5pct"]))

    left, right = st.columns(2)

    with left:
        fig_purchase = px.bar(
            overall,
            x="experiment_group",
            y="purchase_rate_pct",
            text="purchase_rate_pct",
            color="experiment_group",
            title="Purchase Rate by Experiment Group",
        )
        fig_purchase.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig_purchase.update_layout(showlegend=False)
        st.plotly_chart(fig_purchase, use_container_width=True)

        fig_device = px.bar(
            device_summary,
            x="device_type",
            y="purchase_rate_uplift_pct_points",
            text="purchase_rate_uplift_pct_points",
            color="device_type",
            title="Purchase Rate Uplift by Device",
        )
        fig_device.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_device.update_layout(showlegend=False)
        st.plotly_chart(fig_device, use_container_width=True)

    with right:
        fig_rpu = px.bar(
            overall,
            x="experiment_group",
            y="revenue_per_user",
            text="revenue_per_user",
            color="experiment_group",
            title="Revenue Per User by Experiment Group",
        )
        fig_rpu.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
        fig_rpu.update_layout(showlegend=False)
        st.plotly_chart(fig_rpu, use_container_width=True)

        fig_traffic = px.bar(
            traffic_summary,
            x="traffic_source",
            y="purchase_rate_uplift_pct_points",
            text="purchase_rate_uplift_pct_points",
            color="traffic_source",
            title="Purchase Rate Uplift by Traffic Source",
        )
        fig_traffic.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_traffic.update_layout(showlegend=False)
        st.plotly_chart(fig_traffic, use_container_width=True)

    st.subheader("Landing Page Segment Detail")
    st.table(landing_summary.set_index("landing_page"))

    if REPORT_PATH.exists():
        st.subheader("Analyst Summary")
        st.markdown(REPORT_PATH.read_text())


if __name__ == "__main__":
    main()
