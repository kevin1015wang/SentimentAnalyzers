# visuals/plot_sentiment.py
from __future__ import annotations
import csv
import json
import math
import os
from pathlib import Path
from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np  # need linear regression

# config

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
VIS_DIR = ROOT_DIR / "visuals"

VIS_DIR.mkdir(exist_ok=True)

# helpers 
def load_csv(path: Path) -> List[Tuple[str, ...]]:
    """
    Loads our processed CSV files.
    """
    with path.open(newline="", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        header = next(reader)
        return [tuple(row) for row in reader]


def load_tsv(path: Path) -> List[Tuple[str, ...]]:
    """
    Load tab seperated values
    """
    with path.open(newline="", encoding="utf-8") as fp:
        reader = csv.reader(fp, delimiter="\t")
        header = next(reader)
        return [tuple(row) for row in reader]


def plot_monthly_trend():
    """
    Creates monthly average sentiment as a line trend.
    """
    data = json.loads((DATA_DIR / "monthly_sentiment.json").read_text())
    months = [d["month"] for d in data]
    sent = [d["avg_sentiment"] for d in data]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(months, sent, marker="o", linewidth=2)
    ax.set_title("Monthly Average Trump Sentiment (All Platforms)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average sentiment (0‑100)")
    ax.set_xticks(months[:: max(1, len(months)//12) ])  # reduce clutter
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(VIS_DIR / "plot1_monthly_trend.png", dpi=300)
    plt.close(fig)

def plot_weekday_platform():
    """
    Creates weekday sentiment per platform as a grouped bar chart
    """
    rows = load_csv(DATA_DIR / "weekday_sentiment.csv")
    platforms = {row[0] for row in rows}
    weekdays = list(range(7))
    matrix = {plat: [50]*7 for plat in platforms}  # Initialize with neutral sentiment (50)
    for plat, wd, avg in rows:
        if avg:  # Only update if avg is not None or empty
            matrix[plat][int(wd)] = float(avg)

    # Bar positions
    bar_width = 0.4
    x = np.arange(7)

    fig, ax = plt.subplots(figsize=(9, 5))

    for i, plat in enumerate(sorted(platforms)):
        offset = (i - (len(platforms)-1)/2) * bar_width
        ax.bar(x + offset, matrix[plat], width=bar_width, label=plat)

    ax.set_title("Average Sentiment by Weekday and Platform")
    ax.set_xlabel("Weekday (0=Sun)")
    ax.set_ylabel("Average sentiment (0‑100)")
    ax.set_xticks(x)
    ax.set_xticklabels(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    fig.tight_layout()
    fig.savefig(VIS_DIR / "plot2_weekday_platform.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# main

def main():
    print("Generating visualisations in", VIS_DIR.resolve())
    plot_monthly_trend()
    plot_weekday_platform()
    print("Images saved as plot1_ to plot4_...")


if __name__ == "__main__":
    main()
