import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup


print("BATHURST FULL HISTORY BUILDER")


BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

WIKI_API = "https://en.wikipedia.org/w/api.php"

START_YEAR = 1960


def latest_completed_year():
    now = datetime.now(timezone.utc)
    if now.month > 10 or (now.month == 10 and now.day >= 20):
        return now.year
    return now.year - 1


END_YEAR = latest_completed_year()


def clean(x):
    if x is None:
        return None
    if isinstance(x, float) and pd.isna(x):
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x if x else None


def flatten(df):
    cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            c = " ".join([clean(x) for x in c if clean(x)])
        cols.append(clean(c))
    df.columns = cols
    return df


def normalize(df):
    df = flatten(df)
    rename = {}
    for c in df.columns:
        n = c.lower()

        if "pos" in n:
            rename[c] = "pos"
        elif "driver" in n:
            rename[c] = "drivers"
        elif "team" in n or "entrant" in n:
            rename[c] = "team"
        elif "car" in n:
            rename[c] = "car"
        elif "lap" in n:
            rename[c] = "laps"
        elif "grid" in n:
            rename[c] = "grid"
        elif "time" in n:
            rename[c] = "time"
        else:
            rename[c] = n

    return df.rename(columns=rename).dropna(how="all")


def wiki_search(q):
    try:
        r = SESSION.get(WIKI_API, params={
            "action": "opensearch",
            "search": q,
            "limit": 5,
            "namespace": 0,
            "format": "json"
        })
        return r.json()[1]
    except:
        return []


def find_page(year):
    queries = [
        f"{year} Bathurst 1000",
        f"{year} Bathurst 500",
        f"{year} Armstrong 500",
        f"{year} Hardie-Ferodo 500"
    ]

    for q in queries:
        res = wiki_search(q)
        for r in res:
            if str(year) in r:
                return r

    return None


def get_html(title):
    r = SESSION.get(WIKI_API, params={
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json"
    })
    return r.json()["parse"]["text"]["*"]


def extract_tables(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})

    dfs = []
    for t in tables:
        try:
            df = pd.read_html(StringIO(str(t)))[0]
            dfs.append(normalize(df))
        except:
            continue

    return dfs


def find_results_table(tables):
    best = None
    best_score = 0

    for df in tables:
        score = 0
        cols = df.columns

        if "pos" in cols:
            score += 10
        if "drivers" in cols:
            score += 10
        if "car" in cols:
            score += 10
        if "laps" in cols:
            score += 5

        if len(df) > 10:
            score += 10

        if score > best_score:
            best_score = score
            best = df

    return best


def df_to_list(df):
    rows = []
    for _, r in df.iterrows():
        row = {k: clean(v) for k, v in r.items()}
        if any(row.values()):
            rows.append(row)
    return rows


def build_year(year):
    print(f"\n--- {year} ---")

    title = find_page(year)
    if not title:
        print("No page")
        return None

    print("Page:", title)

    html = get_html(title)
    tables = extract_tables(html)

    if not tables:
        print("No tables")
        return None

    results_df = find_results_table(tables)

    results = df_to_list(results_df) if results_df is not None else []

    grid = []
    for r in results:
        if r.get("grid"):
            grid.append({
                "grid": r.get("grid"),
                "drivers": r.get("drivers"),
                "team": r.get("team"),
                "car": r.get("car")
            })

    data = {
        "year": year,
        "source": title,
        "grid": grid,
        "results": results
    }

    out = SEASONS_DIR / f"{year}.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"Saved {year} ({len(results)} results)")

    return {
        "year": year,
        "file": f"seasons/{year}.json",
        "results": len(results)
    }


def main():
    summary = []

    for y in range(START_YEAR, END_YEAR + 1):
        try:
            r = build_year(y)
            if r:
                summary.append(r)
        except Exception as e:
            print("FAILED", y, e)

    INDEX_FILE.write_text(json.dumps(summary, indent=2))
    print("\nDONE")


if __name__ == "__main__":
    main()
