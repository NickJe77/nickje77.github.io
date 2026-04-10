import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO
from pathlib import Path
import re
from datetime import datetime, timezone

print("BATHURST BUILDER (FINAL DRIVER FIX)")

BASE = Path("docs/data/bathurst")
SEASONS = BASE / "seasons"
INDEX = BASE / "index.json"

SEASONS.mkdir(parents=True, exist_ok=True)

START_YEAR = 1960

def latest_year():
    now = datetime.now(timezone.utc)
    return now.year if now.month > 10 else now.year - 1

END_YEAR = latest_year()

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean(x):
    if x is None:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x if x else None


def try_urls(year):
    names = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Armstrong_500",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000"
    ]

    for n in names:
        url = f"https://en.wikipedia.org/wiki/{n}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200 and "Bathurst" in r.text:
            return url, r.text

    return None, None


def extract_tables(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})

    dfs = []
    for t in tables:
        try:
            df = pd.read_html(StringIO(str(t)))[0]
            dfs.append(df)
        except:
            continue

    return dfs


# 🔥 NORMALIZE + MERGE DRIVER COLUMNS
def normalize(df):
    df.columns = [clean(c).lower() for c in df.columns]

    rename = {}
    driver_cols = []

    for c in df.columns:

        if "pos" in c:
            rename[c] = "pos"

        elif "driver" in c:
            driver_cols.append(c)

        elif "team" in c:
            rename[c] = "team"

        elif "car" in c:
            rename[c] = "car"

        elif "lap" in c:
            rename[c] = "laps"

        elif "grid" in c:
            rename[c] = "grid"

    df = df.rename(columns=rename)

    # merge driver columns into one string
    if driver_cols:
        df["drivers"] = df[driver_cols].apply(
            lambda row: " / ".join([clean(x) for x in row if clean(x)]),
            axis=1
        )
        df = df.drop(columns=driver_cols)

    return df


def best_results(tables):
    best = None
    score = 0

    for df in tables:
        df = normalize(df)

        s = 0
        if "pos" in df.columns:
            s += 10
        if "drivers" in df.columns:
            s += 10
        if "car" in df.columns:
            s += 10
        if len(df) > 10:
            s += 10

        if s > score:
            score = s
            best = df

    return best


# 🔥 FINAL DRIVER PARSER (ROBUST)
def split_drivers(val):
    if not val:
        return []

    val = clean(val)

    # remove brackets content
    val = re.sub(r"\([^)]*\)", "", val)

    # normalize separators
    val = val.replace(" and ", "/")
    val = val.replace(";", "/")

    parts = re.split(r"/", val)

    drivers = []

    for p in parts:
        p = clean(p)

        if not p:
            continue

        # FIX reversed names: "Brock, Peter"
        if "," in p:
            bits = [b.strip() for b in p.split(",")]
            if len(bits) == 2:
                p = f"{bits[1]} {bits[0]}"

        # ignore junk
        if len(p) < 3:
            continue

        drivers.append(p)

    # remove duplicates
    seen = set()
    out = []
    for d in drivers:
        key = d.lower()
        if key not in seen:
            seen.add(key)
            out.append(d)

    return out


def df_to_json(df):
    rows = []

    for _, r in df.iterrows():
        row = {k: clean(v) for k, v in r.items()}

        if "drivers" in row:
            row["drivers"] = split_drivers(row["drivers"])

        if any(row.values()):
            rows.append(row)

    return rows


def build_year(year):
    print(f"\n--- {year} ---")

    url, html = try_urls(year)

    if not html:
        print("No page")
        return None

    print("URL:", url)

    tables = extract_tables(html)

    if not tables:
        print("No tables")
        return None

    res_df = best_results(tables)

    if res_df is None:
        print("No results table")
        return None

    results = df_to_json(res_df)

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
        "url": url,
        "grid": grid,
        "results": results
    }

    file = SEASONS / f"{year}.json"
    file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"Saved {year}")

    return {"year": year, "file": f"seasons/{year}.json"}


def main():
    summary = []

    for y in range(START_YEAR, END_YEAR + 1):
        try:
            r = build_year(y)
            if r:
                summary.append(r)
        except Exception as e:
            print("FAIL", y, e)

    INDEX.write_text(json.dumps(summary, indent=2))
    print("\nDONE")


if __name__ == "__main__":
    main()
