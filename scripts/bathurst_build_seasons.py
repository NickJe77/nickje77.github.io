import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("BATHURST SEASONS BUILDER (DEBUG LOCKED)")

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
    print(f"\n====================")
    print(f"YEAR: {year}")

    url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"

    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print("❌ Page missing")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        tables = soup.find_all("table", {"class": "wikitable"})
        print(f"Found {len(tables)} tables")

        target = None

        # 🔥 PRINT HEADERS FOR DEBUG
        for i, t in enumerate(tables):
            headers = [clean(th.get_text()) for th in t.find_all("th")]
            header_text = " | ".join(headers).lower()

            print(f"\nTable {i} headers:")
            print(header_text)

            if (
                "driver" in header_text
                and ("pos" in header_text or "position" in header_text)
                and "car" in header_text
            ):
                print("👉 THIS IS THE RESULTS TABLE")
                target = t
                break

        if target is None:
            print("❌ NO MATCHING TABLE FOUND")
            continue

        rows = target.find_all("tr")

        headers = [clean(th.get_text()) for th in rows[0].find_all("th")]

        pos_idx = None
        car_idx = None

        for i, h in enumerate(headers):
            if not h:
                continue
            h = h.lower()

            if "pos" in h or "position" in h:
                pos_idx = i

            if "car" in h:
                car_idx = i

        print(f"Detected → pos:{pos_idx}, car:{car_idx}")

        results = []

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            try:
                pos = clean(cols[pos_idx].get_text()) if pos_idx is not None and pos_idx < len(cols) else None
                car = clean(cols[car_idx].get_text()) if car_idx is not None and car_idx < len(cols) else None

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

        print(f"Extracted {len(results)} rows")

        # force winner
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

        print("✅ SAVED")

    except Exception as e:
        print("❌ ERROR:", e)
