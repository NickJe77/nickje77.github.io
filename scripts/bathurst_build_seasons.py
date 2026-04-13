import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (CORRECT VERSION)")

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
    x = re.sub(r"\[[^\]]+\]", "", str(x))
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()


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


def find_results_table(soup):
    for header in soup.find_all(["h2", "h3"]):
        title = header.get_text().lower()

        if "classification" in title or "race results" in title:
            table = header.find_next("table", class_="wikitable")
            if table:
                return table

    return None


def get_column_indexes(table):
    headers = table.find_all("th")
    cols = [clean(h.get_text()).lower() for h in headers]

    pos_idx = None
    driver_idx = None
    car_idx = None

    for i, c in enumerate(cols):
        if "pos" in c:
            pos_idx = i
        elif "driver" in c:
            driver_idx = i
        elif "car" in c or "team" in c:
            car_idx = i

    return pos_idx, driver_idx, car_idx


def extract_drivers(cell):
    drivers = []

    # prefer links
    for a in cell.find_all("a"):
        name = clean(a.get_text())
        if name and " " in name:
            drivers.append(name)

    # fallback split
    if not drivers:
        text = clean(cell.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+", text)

        for p in parts:
            p = clean(p)
            if p and " " in p:
                drivers.append(p)

    # dedupe
    final = []
    seen = set()

    for d in drivers:
        key = d.lower()
        if key not in seen:
            seen.add(key)
            final.append(d)

    return final[:2]


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    table = find_results_table(soup)

    if not table:
        print(f"❌ No results table {year}")
        return None

    pos_idx, driver_idx, car_idx = get_column_indexes(table)

    if pos_idx is None or driver_idx is None:
        print(f"❌ Missing columns {year}")
        return None

    results = []

    for row in table.find_all("tr"):
        cells = row.find_all("td")

        if not cells:
            continue

        cols = [clean(c.get_text(" ", strip=True)) for c in cells]

        try:
            finish = int(cols[pos_idx])
        except:
            continue

        drivers = extract_drivers(cells[driver_idx])

        if not drivers:
            continue

        car = None
        if car_idx is not None and car_idx < len(cols):
            car = cols[car_idx]

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    if not results:
        print(f"⚠️ No results {year}")
        return None

    results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": results
    }


# BUILD
seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    winner_drivers = results[0]["drivers"] if results else []
    winner_car = results[0]["car"] if results else None

    with open(BASE / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open(SEASONS_DIR / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    seasons.append({
        "year": year,
        "winner_drivers": winner_drivers,
        "winner_car": winner_car
    })

    print(f"✅ Saved {year} ({len(results)} rows)")
    time.sleep(1)


seasons.sort(key=lambda x: x["year"])

with open(BASE / "seasons.json", "w", encoding="utf-8") as f:
    json.dump(seasons, f, indent=2, ensure_ascii=False)

with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": seasons
    }, f, indent=2, ensure_ascii=False)

print("🔥 DONE")
