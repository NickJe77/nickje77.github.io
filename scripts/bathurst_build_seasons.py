import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("BATHURST SEASONS BUILDER")

BASE = Path("docs/data/bathurst")
SEASONS = BASE / "seasons"
SEASONS.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# load winners (SOURCE OF TRUTH)
with open(BASE / "winners.json") as f:
    winners = {x["year"]: x for x in json.load(f)}

def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", x)
    return re.sub(r"\s+", " ", x).strip()

def extract_drivers(text):
    if not text:
        return []
    return [clean(x) for x in re.split(r"/|,| and ", text) if clean(x)]

for year in sorted(winners.keys()):
    print(f"Processing {year}")

    url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"

    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print("❌ Page missing")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        tables = soup.find_all("table", {"class": "wikitable"})

        target = None
        for table in tables:
            if "Driver" in table.text or "Drivers" in table.text:
                target = table
                break

        season = []

        if target:
            rows = target.find_all("tr")[1:]

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                try:
                    pos = clean(cols[0].get_text())
                    car = clean(cols[2].get_text())

                    drivers = []
                    for c in cols:
                        drivers.extend(extract_drivers(c.get_text()))

                    drivers = list(dict.fromkeys(drivers))

                    if not drivers:
                        continue

                    season.append({
                        "position": pos,
                        "car": car,
                        "drivers": drivers
                    })

                except:
                    continue

        # 🔥 FORCE correct winner
        winner = winners[year]
        if season:
            season[0]["drivers"] = winner["drivers"]

        out = SEASONS / f"{year}.json"
        with open(out, "w") as f:
            json.dump({
                "year": year,
                "results": season,
                "winner": winner
            }, f, indent=2)

        print("✅ Saved")

    except Exception as e:
        print("❌ Failed", e)
