import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("BATHURST SEASONS BUILDER (FINAL)")

BASE = Path("docs/data/bathurst")
SEASONS = BASE / "seasons"
SEASONS.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    return re.sub(r"\s+", " ", x).strip()

def extract_drivers(text):
    if not text:
        return []
    return [clean(x) for x in re.split(r"/|,| and ", text) if clean(x)]

# load winners (CRITICAL)
with open(BASE / "winners.json") as f:
    winners = {x["year"]: x for x in json.load(f)}

for year in winners.keys():
    print(f"Processing {year}")

    url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"

    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print("❌ Missing page")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        tables = soup.find_all("table", {"class": "wikitable"})

        target = None
        for t in tables:
            if "Driver" in t.text or "Drivers" in t.text:
                target = t
                break

        results = []

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

                    results.append({
                        "position": pos,
                        "car": car,
                        "drivers": drivers
                    })

                except:
                    continue

        # 🔥 FORCE correct winner
        winner = winners[year]

        if results:
            results[0]["drivers"] = winner["drivers"]

        with open(SEASONS / f"{year}.json", "w") as f:
            json.dump({
                "year": year,
                "winner": winner,
                "results": results
            }, f, indent=2)

        print("✅ Saved")

    except Exception as e:
        print("❌ Failed", e)
