import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (ENTRY-BASED – FULL GRID + CO-DRIVERS FIXED)")

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

    out = []
    for p in parts:
        p = clean(p)
        if p and len(p.split()) >= 2:
            out.append(p)

    return out[:2]


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000",
        f"{year}_AMP_Bathurst_1000"
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
        title = header.get_text().lower()
        if "entry" in title or "starting grid" in title:
            return header.find_next("table")
    return None


def find_results_table(soup):
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()
        if "driver" in text and ("pos" in text or "position" in text):
            return table
    return None


# 🔥 BUILD FULL GRID FROM ENTRY LIST
def build_entry_grid(entry_table):
    grid = []

    if not entry_table:
        return grid

    for row in entry_table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        cols = [clean(td.get_text(" ", strip=True)) for td in tds]

        car_no = None
        drivers = []
        car = None

        for c in cols:
            if not car_no and c and c.isdigit():
                car_no = c

            d = split_drivers(c)
            if len(d) >= 2:
                drivers = d

        for c in cols:
            if c and c not in drivers and c != car_no:
                car = c
                break

        if drivers:
            grid.append({
                "car_no": car_no,
                "drivers": drivers,
                "car": car,
                "finish": None
            })

    return grid


# 🔥 APPLY RESULTS ON TOP
def apply_results(grid, results_table):
    if not results_table:
        return grid

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

        # 🔥 MATCH BY DRIVER NAME (fallback)
        for entry in grid:
            for d in entry["drivers"]:
                if d in text:
                    entry["finish"] = finish
                    break

    return grid


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

    grid = build_entry_grid(entry_table)

    if not grid:
        print(f"❌ No entry grid {year}")
        return None

    grid = apply_results(grid, results_table)

    # remove entries without finish if needed
    grid = [g for g in grid if g["finish"] is not None]

    grid.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": grid
    }


# BUILD
seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

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
