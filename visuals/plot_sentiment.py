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

"""def plot_karma_scatter():
    
    #Reddit karma vs sentiment as scatter plot with regression
    
    rows = load_tsv(DATA_DIR / "karma_vs_sentiment.tsv")
    
    # Filter out invalid rows and convert to numpy arrays
    valid_rows = [(int(k), int(s)) for k, s in rows if k and s and k != '0' and s != '0']
    if not valid_rows:
        print("Warning: No valid data points found for karma vs sentiment plot")
        return
        
    karma = np.array([k for k, _ in valid_rows])
    sent = np.array([s for _, s in valid_rows])

    # Only attempt regression if we have enough valid points
    if len(karma) >= 2:
        try:
            slope, intercept = np.polyfit(karma, sent, 1)
            line_x = np.linspace(karma.min(), karma.max(), 100)
            line_y = slope * line_x + intercept
            
            # Calculate R squared
            r_value = np.corrcoef(karma, sent)[0, 1]
            r_squared = r_value ** 2
        except (np.linalg.LinAlgError, ValueError) as e:
            print(f"Warning: Could not compute regression line: {e}")
            line_x = line_y = None
            r_squared = None
    else:
        line_x = line_y = None
        r_squared = None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(karma, sent, alpha=0.6, s=20)
    
    if line_x is not None:
        ax.plot(line_x, line_y, linestyle="--", linewidth=1.5)
        if r_squared is not None:
            ax.text(0.05, 0.95, f"$R^2$ = {r_squared:.2f}", transform=ax.transAxes,
                    verticalalignment="top")

    ax.set_xscale("log")
    ax.set_title("Reddit: User Karma vs Trump Sentiment")
    ax.set_xlabel("User karma (log scale)")
    ax.set_ylabel("Sentiment score (0‑100)")
    fig.tight_layout()
    fig.savefig(VIS_DIR / "plot3_karma_scatter.png", dpi=300)
    plt.close(fig)
"""

def plot_subreddit_bar():
    """
    Creates the most extreme subreddits as horizontal bar chart
    """
    rows = load_csv(DATA_DIR / "subreddit_sentiment.txt")

def _load_pipe(path: Path):
    """
    Custom parser for plot_subreddit_bar
    """
    with path.open(encoding="utf-8") as fp:
        next(fp)  # header
        parsed = []
        for line in fp:
            subreddit, n_posts, avg = line.strip().split("|")
            parsed.append((subreddit, int(n_posts), float(avg)))
    return parsed


def plot_subreddit_bar():
    parsed = _load_pipe(DATA_DIR / "subreddit_sentiment.txt")

    # sort by avg sentiment
    parsed.sort(key=lambda x: x[2])
    bottom10 = parsed[:10]
    top10 = parsed[-10:]
    combined = bottom10 + top10[::-1]  # negative first

    labels = [s for s, _, _ in combined]
    scores = [avg for _, _, avg in combined]

    fig, ax = plt.subplots(figsize=(10, 7))
    y = np.arange(len(labels))
    ax.barh(y, scores)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Average sentiment (0‑100)")
    ax.set_title("Most Negative vs Most Positive Subreddits (≥20 posts)")
    for i, v in enumerate(scores):
        ax.text(v + (2 if v >= 0 else -2), i, f"{v:.1f}", va="center",
                ha="left" if v >= 0 else "right")
    fig.tight_layout()
    fig.savefig(VIS_DIR / "plot4_subreddit_bar.png", dpi=300)
    plt.close(fig)

# main

def main():
    print("Generating visualisations in", VIS_DIR.resolve())
    plot_monthly_trend()
    plot_weekday_platform()
    #plot_karma_scatter()
    plot_subreddit_bar()
    print("Images saved as plot1_ to plot4_...")


if __name__ == "__main__":
    main()
