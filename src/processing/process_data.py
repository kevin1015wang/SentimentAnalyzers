from __future__ import annotations
import os
import csv
import json
import sqlite3
from pathlib import Path
from typing import Sequence, Any

# Config

ROOT_DIR: Path = Path(__file__).resolve().parents[2]
DB_PATH:   Path = ROOT_DIR / "data" / "project.db"
OUT_DIR:   Path = ROOT_DIR / "data"

OUT_DIR.mkdir(exist_ok=True)


# utilities

def write_csv(path: Path, header: Sequence[str], rows: Sequence[tuple[Any, ...]],
              delimiter: str = ",") -> None:
    """Write rows with header to path using a delimiter."""
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, delimiter=delimiter)
        writer.writerow(header)
        writer.writerows(rows)


def write_json(path: Path, obj: Any) -> None:
    """Write any object to a given path."""
    with path.open("w", encoding="utf-8") as fp:
        json.dump(obj, fp, indent=2, ensure_ascii=False)


# calculations 

def calc_weekday_sentiment(cur: sqlite3.Cursor) -> None:
    """
    Get average Trump sentiment by weekday and platform.

    result: platform, weekday (0=Sun ... 6=Sat), avg_sentiment
    """
    query = """
        SELECT platform,
               weekday,
               ROUND(AVG(sentiment), 2) AS avg_sentiment
        FROM (
            SELECT 'Reddit'      AS platform,
                   strftime('%w', post_date) AS weekday,
                   trump_sentiment            AS sentiment
            FROM   reddit_posts
            WHERE  trump_sentiment IS NOT NULL

            UNION ALL

            SELECT 'Instagram',
                   strftime('%w', post_date),
                   trump_sentiment
            FROM   instagram_posts
            WHERE  trump_sentiment IS NOT NULL
        )
        GROUP BY platform, weekday
        ORDER BY platform, weekday;
    """
    cur.execute(query)
    rows = cur.fetchall()
    write_csv(
        OUT_DIR / "weekday_sentiment.csv",
        header=("platform", "weekday", "avg_sentiment"),
        rows=rows,
    )

def calc_monthly_sentiment(cur: sqlite3.Cursor) -> None:
    """
    Overall monthly sentiment trend with both platforms.
    Result: a JSON list of {"month": "...", "avg_sentiment": ...}
    """
    query = """
        SELECT month,
               ROUND(AVG(sentiment), 2) AS avg_sentiment
        FROM (
            SELECT strftime('%Y-%m', post_date) AS month,
                   trump_sentiment AS sentiment
            FROM   reddit_posts
            WHERE  trump_sentiment IS NOT NULL

            UNION ALL

            SELECT strftime('%Y-%m', post_date),
                   trump_sentiment
            FROM   instagram_posts
            WHERE  trump_sentiment IS NOT NULL
        )
        GROUP BY month
        ORDER BY month;
    """
    cur.execute(query)
    rows = cur.fetchall()
    data = [{"month": m, "avg_sentiment": s} for m, s in rows]
    write_json(OUT_DIR / "monthly_sentiment.json", data)

# main

def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        print("Making Part‑3 calculation files...")
        calc_weekday_sentiment(cur)
        calc_monthly_sentiment(cur)

    print("All files written to", OUT_DIR.resolve())


if __name__ == "__main__":
    main()