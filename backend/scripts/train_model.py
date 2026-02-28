"""Train model and produce analytics plots.

Usage:
    python backend/scripts/train_model.py --input data/sample_tasks.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from backend.app.services.analytics import generate_analytics
from backend.app.services.ml import train_best_time_model
from backend.app.services.preprocess import preprocess_tasks


def main(input_path: str) -> None:
    output_dir = Path("models/plots")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    clean = preprocess_tasks(df)

    metrics = train_best_time_model(clean)
    analytics = generate_analytics(clean)

    plt.figure(figsize=(9, 4))
    sns.countplot(data=clean[clean["status"] == "completed"], x="completed_hour", color="#4C72B0")
    plt.title("Completed Tasks by Hour")
    plt.xlabel("Hour")
    plt.ylabel("Completed Task Count")
    plt.tight_layout()
    plt.savefig(output_dir / "productivity_by_hour.png")
    plt.close()

    weekly = (
        clean.assign(week=clean["assigned_time"].dt.isocalendar().week)
        .groupby("week")["completed_flag"]
        .mean()
        .reset_index()
    )
    plt.figure(figsize=(8, 4))
    sns.lineplot(data=weekly, x="week", y="completed_flag", marker="o")
    plt.title("Week-over-Week Completion Rate")
    plt.ylabel("Completion Rate")
    plt.tight_layout()
    plt.savefig(output_dir / "week_over_week_completion.png")
    plt.close()

    print("Training complete.")
    print("Metrics:", metrics)
    print("Analytics summary:", analytics)
    print(f"Plots saved to {output_dir.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_tasks.csv")
    args = parser.parse_args()
    main(args.input)
