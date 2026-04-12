import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("BATHURST FULL FIELD BUILDER (AFL TABLES)")

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


def slug_year(y):
    return str(y)


def fetch_year(year):
    url = f"https://afltables.com/motor/bathurst/bathurst_{year}.html"

    print(f"Fetching {year}...")

    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Failed {year}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table")
    if not table:
        print(f"❌ No table {year}")
        return None

    rows = table.find_all("tr")

    results = []

    for r in rows:
        cols = [clean(c.get_text()) for c in r.find_all("td")]

        if len(cols) < 5:
            continue

        try:
            finish = int(cols[0])
        except:
            continue

        drivers_raw = cols[2]
        car = cols[3]
        laps = cols[4]

        # split drivers properly
        drivers = re.split(r"/|,| and ", drivers_raw)
        drivers = [d.strip() for d in drivers if d.strip()]

        results.append({
            "finish": finish,
            "grid": None,
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
        continue

    out = BASE / f"{y}.json"

    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    built += 1

print(f"✅ BUILT {built} YEARS")
