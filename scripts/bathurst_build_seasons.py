import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("BATHURST FULL FIELD BUILDER (BRUTE FORCE FIX)")

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
    parts = re.split(r"/|,| and | & |\+", text)
    return [clean(p) for p in parts if clean(p)]


def fetch_year(year):
    url = f"https://afltables.com/motor/bathurst/bathurst_{year}.html"
    print(f"Fetching {year}...")

    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Failed {year}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    tables = soup.find_all("table")

    results = []

    for table in tables:
        rows = table.find_all("tr")

        for r in rows:
            cols = [clean(c.get_text()) for c in r.find_all("td")]

            if len(cols) < 3:
                continue

            # FIRST COLUMN must be a finishing position
            try:
                finish = int(cols[0])
            except:
                continue

            # Try to detect driver column
            drivers_raw = None
            car = None
            laps = None

            if len(cols) >= 5:
                drivers_raw = cols[2]
                car = cols[3]
                laps = cols[4]
            elif len(cols) >= 3:
                drivers_raw = cols[1]
                car = cols[2]

            drivers = split_drivers(drivers_raw)

            # skip junk rows
            if not drivers:
                continue

            results.append({
                "finish": finish,
                "drivers": drivers,
                "car": car,
                "laps": laps
            })

    # REMOVE DUPLICATES (AFL Tables repeats stuff sometimes)
    unique = {}
    for r in results:
        key = (r["finish"], tuple(r["drivers"]))
        unique[key] = r

    final_results = list(unique.values())
    final_results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final_results
    }


built = 0

for y in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(y)

    if not data or not data["results"]:
        print(f"⚠️ No data {y}")
        continue

    out = BASE / f"{y}.json"

    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved {y} ({len(data['results'])} drivers)")
    built += 1

print(f"🔥 BUILT {built} YEARS")
