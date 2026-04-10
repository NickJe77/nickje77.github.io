import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST FULL SCRAPER (WIKIPEDIA)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2026

for year in range(START_YEAR, END_YEAR + 1):

    try:
        print(f"Scraping {year}")

        url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"
        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            print(f"Skip {year} (no page)")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # find results table
        tables = soup.find_all("table", {"class": "wikitable"})
        if not tables:
            print(f"No table {year}")
            continue

        table = tables[0]
        rows = table.find_all("tr")[1:]

        results = []

        for r in rows:
            cols = [c.get_text(" ", strip=True) for c in r.find_all(["td","th"])]

            if len(cols) < 5:
                continue

            try:
                finish = int(cols[0])
            except:
                continue

            driver_text = cols[1]

            # 🔥 split co-drivers properly
            drivers = re.split(r"/|,| and ", driver_text)
            drivers = [d.strip() for d in drivers if d.strip()]

            car = cols[2]
            laps = cols[3]
            time_val = cols[4]

            try:
                laps = int(re.findall(r"\d+", laps)[0])
            except:
                laps = None

            results.append({
                "finish": finish,
                "grid": None,  # wiki rarely has grid cleanly
                "drivers": drivers,
                "car": car,
                "laps": laps,
                "time": time_val
            })

        if not results:
            print(f"No results {year}")
            continue

        winners = results[0]["drivers"]

        race = {
            "year": year,
            "track": "Mount Panorama",
            "results": results,
            "winners": winners
        }

        file = BASE / f"{year}.json"
        with open(file, "w") as f:
            json.dump(race, f, indent=2)

        print(f"Saved {year}")

        time.sleep(1)

    except Exception as e:
        print(f"FAILED {year}", e)

print("DONE")
