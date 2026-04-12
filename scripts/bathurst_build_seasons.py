import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("BATHURST FULL FIELD BUILDER (FIXED AFL TABLES)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()


def split_drivers(text):
    if not text:
        return []

    # Handle ALL formats AFL Tables uses
    parts = re.split(r"/|,| and | & |\+", text)
    return [clean(p) for p in parts if clean(p)]


def get_results_table(soup):
    tables = soup.find_all("table")

    for table in tables:
        headers = [clean(th.get_text()) for th in table.find_all("th")]

        if not headers:
            continue

        header_str = " ".join(headers).lower()

        # identify correct table
        if "pos" in header_str or "fin" in header_str or "place" in header_str:
            if "driver" in header_str or "car" in header_str:
                return table

    return None


def fetch_year(year):
    url = f"https://afltables.com/motor/bathurst/bathurst_{year}.html"
    print(f"Fetching {year}...")

    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Failed {year}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    table = get_results_table(soup)

    if not table:
        print(f"❌ No results table {year}")
        return None

    rows = table.find_all("tr")

    results = []

    for r in rows:
        cols = [clean(c.get_text()) for c in r.find_all("td")]

        if len(cols) < 4:
            continue

        # position
        try:
            finish = int(cols[0])
        except:
            continue

        # AFL Tables structure varies by year
        drivers_raw = None
        car = None
        laps = None

        if len(cols) >= 5:
            drivers_raw = cols[2]
            car = cols[3]
            laps = cols[4]
        else:
            drivers_raw = cols[1]
            car = cols[2] if len(cols) > 2 else None

        drivers = split_drivers(drivers_raw)

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car,
            "laps": laps
        })

    return {
        "year": year,
        "results": results
    }


built = 0

for y in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(y)

    if not data or not data["results"]:
        print(f"⚠️ Skipped {y}")
        continue

    out = BASE / f"{y}.json"

    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved {y}")
    built += 1

print(f"🔥 BUILT {built} YEARS")
