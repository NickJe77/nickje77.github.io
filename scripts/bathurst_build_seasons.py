import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("BATHURST SEASONS BUILDER (POSITION FIXED)")

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

# load winners
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
            rows = target.find_all("tr")

            # 🔥 FIND HEADER
            headers = [clean(th.get_text()) for th in rows[0].find_all("th")]

            pos_idx = None
            car_idx = None

            for i, h in enumerate(headers):
                if h and ("Pos" in h or "Position" in h):
                    pos_idx = i
                if h and "Car" in h:
                    car_idx = i

            # fallback if not found
            if pos_idx is None:
                pos_idx = 0
            if car_idx is None:
                car_idx = 2 if len(headers) > 2 else 1

            # 🔥 PROCESS ROWS
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                try:
                    pos = clean(cols[pos_idx].get_text()) if pos_idx < len(cols) else None
                    car = clean(cols[car_idx].get_text()) if car_idx < len(cols) else None

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
            results[0]["position"] = "1"

        with open(SEASONS / f"{year}.json", "w") as f:
            json.dump({
                "year": year,
                "winner": winner,
                "results": results
            }, f, indent=2)

        print("✅ Saved")

    except Exception as e:
        print("❌ Failed", e)
