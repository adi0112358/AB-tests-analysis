from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "experiment_events.csv"


def _choice(rng: np.random.Generator, values: list[str], probs: list[float], size: int) -> np.ndarray:
    return rng.choice(values, size=size, p=probs)


def build_dataset(row_count: int = 6000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    experiment_group = np.array(["control"] * (row_count // 2) + ["treatment"] * (row_count - row_count // 2))
    rng.shuffle(experiment_group)

    device_type = _choice(rng, ["Mobile", "Desktop", "Tablet"], [0.56, 0.35, 0.09], row_count)
    traffic_source = _choice(rng, ["Paid Search", "Organic Search", "Email", "Social"], [0.31, 0.33, 0.17, 0.19], row_count)
    region = _choice(rng, ["North", "South", "West", "East"], [0.24, 0.27, 0.26, 0.23], row_count)
    landing_page = _choice(rng, ["Pricing", "Features", "Homepage"], [0.38, 0.34, 0.28], row_count)

    sessions = rng.poisson(3.2, row_count) + 1
    sessions += np.where(traffic_source == "Email", 1, 0)
    sessions = np.clip(sessions, 1, 12)

    avg_session_duration = rng.normal(214, 48, row_count)
    avg_session_duration += np.where(device_type == "Desktop", 24, 0)
    avg_session_duration += np.where(experiment_group == "treatment", 12, 0)
    avg_session_duration = np.clip(avg_session_duration, 45, None).round(1)

    pages_viewed = rng.normal(5.8, 1.6, row_count)
    pages_viewed += np.where(landing_page == "Features", 0.6, 0)
    pages_viewed += np.where(experiment_group == "treatment", 0.35, 0)
    pages_viewed = np.clip(pages_viewed, 1.0, None).round(1)

    signup_logit = -1.7
    signup_logit += np.where(device_type == "Desktop", 0.18, 0)
    signup_logit += np.where(traffic_source == "Email", 0.42, 0)
    signup_logit += np.where(traffic_source == "Organic Search", 0.14, 0)
    signup_logit += np.where(landing_page == "Pricing", 0.22, 0)
    signup_logit += 0.12 * np.minimum(sessions, 5)
    signup_logit += 0.11 * (pages_viewed - 5)
    signup_logit += np.where(experiment_group == "treatment", 0.24, 0)
    signup_logit += np.where((experiment_group == "treatment") & (device_type == "Mobile"), 0.1, 0)

    signup_probability = 1 / (1 + np.exp(-signup_logit))
    signed_up = rng.binomial(1, signup_probability)

    purchase_logit = -2.55
    purchase_logit += 0.95 * signed_up
    purchase_logit += np.where(device_type == "Desktop", 0.15, 0)
    purchase_logit += np.where(traffic_source == "Email", 0.28, 0)
    purchase_logit += np.where(traffic_source == "Social", -0.12, 0)
    purchase_logit += np.where(landing_page == "Pricing", 0.22, 0)
    purchase_logit += np.where(experiment_group == "treatment", 0.18, 0)
    purchase_logit += np.where((experiment_group == "treatment") & (traffic_source == "Email"), 0.12, 0)
    purchase_logit += 0.05 * np.minimum(sessions, 6)

    purchase_probability = 1 / (1 + np.exp(-purchase_logit))
    purchased = rng.binomial(1, purchase_probability)

    order_value = rng.normal(108, 26, row_count)
    order_value += np.where(device_type == "Desktop", 9, 0)
    order_value += np.where(landing_page == "Pricing", 6, 0)
    order_value += np.where(experiment_group == "treatment", 4, 0)
    order_value = np.clip(order_value, 25, None).round(2)
    revenue = (order_value * purchased).round(2)

    user_ids = [f"USER-{index:05d}" for index in range(1, row_count + 1)]

    return pd.DataFrame(
        {
            "user_id": user_ids,
            "experiment_group": experiment_group,
            "device_type": device_type,
            "traffic_source": traffic_source,
            "region": region,
            "landing_page": landing_page,
            "sessions": sessions.astype(int),
            "avg_session_duration_sec": avg_session_duration,
            "pages_viewed": pages_viewed,
            "signed_up": signed_up.astype(int),
            "purchased": purchased.astype(int),
            "order_value": order_value,
            "revenue": revenue,
        }
    )


def main() -> None:
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset()
    dataset.to_csv(RAW_DATA_PATH, index=False)
    control_purchase = dataset.loc[dataset["experiment_group"] == "control", "purchased"].mean() * 100
    treatment_purchase = dataset.loc[dataset["experiment_group"] == "treatment", "purchased"].mean() * 100
    print(f"Saved {len(dataset)} rows to {RAW_DATA_PATH}")
    print(f"Control purchase rate: {control_purchase:.2f}%")
    print(f"Treatment purchase rate: {treatment_purchase:.2f}%")


if __name__ == "__main__":
    main()
