import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FINAL – HYBRID SYSTEM)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"

BASE.mkdir(parents=True, exist_ok=True)
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def split_drivers(text):
    text = clean(text) or ""
    parts = re.split(r"/|,| and | & |\+", text)

    return [clean(p) for p in parts if p and len(p.split()) >= 2][:2]


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500"
    ]

    for p in patterns:
        url = f"https://en.wikipedia.org/wiki/{p}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return url
        except:
            pass

    return None


def find_entry_table(soup):
    for header in soup.find_all(["h2", "h3"]):
        if "entry" in header.get_text().lower():
            return header.find_next("table")
    return None


def find_results_table(soup):
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()
        if "driver" in text and ("pos" in text or "position" in text):
            return table
    return None


# 🔥 ENTRY SYSTEM
def build_entry_grid(entry_table):
    grid = []

    for row in entry_table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        cols = [clean(td.get_text(" ", strip=True)) for td in tds]

        drivers = []
        for c in cols:
            d = split_drivers(c)
            if len(d) >= 2:
                drivers = d

        if drivers:
            grid.append({
                "drivers": drivers,
                "car": None,
                "finish": None
            })

    return grid


def apply_results(grid, results_table):
    for row in results_table.find_all("tr"):
        tds = row.find_all("td")
        ths = row.find_all("th")

        if not tds:
            continue

        finish = None

        if ths:
            f = clean(ths[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            f = clean(tds[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            continue

        text = row.get_text(" ", strip=True)

        for entry in grid:
            for d in entry["drivers"]:
                if d and d in text:
                    entry["finish"] = finish
                    break

    return [g for g in grid if g["finish"] is not None]


# 🔥 FALLBACK SYSTEM
def parse_results_only(results_table):
    results = []

    for row in results_table.find_all("tr"):
        tds = row.find_all("td")
        ths = row.find_all("th")

        if not tds:
            continue

        finish = None

        if ths:
            f = clean(ths[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            f = clean(tds[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            continue

        text = row.get_text(" ", strip=True)
        drivers = split_drivers(text)

        if not drivers:
            continue

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": None
        })

    return results


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    entry_table = find_entry_table(soup)
    results_table = find_results_table(soup)

    # ✅ ENTRY FIRST
    if entry_table:
        grid = build_entry_grid(entry_table)
        results = apply_results(grid, results_table)

        if results:
            print(f"✅ Entry system {year}")
            return {"year": year, "results": sorted(results, key=lambda x: x["finish"])}

    # 🔥 FALLBACK
    if results_table:
        results = parse_results_only(results_table)

        if results:
            print(f"⚠️ Fallback results {year}")
            return {"year": year, "results": sorted(results, key=lambda x: x["finish"])}

    print(f"❌ No data {year}")
    return None


# BUILD
seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    if not results:
        continue

    with open(BASE / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open(SEASONS_DIR / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    seasons.append({
        "year": year,
        "winner_drivers": results[0]["drivers"],
        "winner_car": results[0]["car"]
    })

    print(f"✅ Saved {year} ({len(results)} rows)")
    time.sleep(1)

seasons.sort(key=lambda x: x["year"])

with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": seasons
    }, f, indent=2, ensure_ascii=False)

print("🔥 DONE")
