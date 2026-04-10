import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST FULL SCRAPER")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Bathurst race index
INDEX_URL = "https://www.racing-reference.info/tracks/Mount_Panorama/"

res = requests.get(INDEX_URL, headers=HEADERS)
soup = BeautifulSoup(res.text, "html.parser")

links = soup.select("table tr a")

race_links = []

for a in links:
    href = a.get("href", "")
    if "/race/" in href:
        race_links.append("https://www.racing-reference.info" + href)

print(f"Found {len(race_links)} races")

# -------------------------------------------------
# SCRAPE EACH RACE
# -------------------------------------------------

for url in race_links:

    try:
        print("Scraping:", url)

        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1").text.strip()

        year_match = re.search(r"\b(19|20)\d{2}\b", title)
        if not year_match:
            continue

        year = int(year_match.group(0))

        table = soup.select_one("table")
        if not table:
            continue

        rows = table.select("tr")[1:]

        results = []

        for r in rows:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]

            if len(cols) < 6:
                continue

            finish = cols[0]
            start = cols[1]
            driver = cols[2]
            car = cols[3]
            laps = cols[4]
            status = cols[5]

            # 🔥 SPLIT CO-DRIVERS (CRITICAL FIX)
            drivers = re.split(r"/|,| and ", driver)

            drivers = [d.strip() for d in drivers if d.strip()]

            results.append({
                "finish": int(finish) if finish.isdigit() else None,
                "grid": int(start) if start.isdigit() else None,
                "drivers": drivers,
                "car": car,
                "laps": int(laps) if laps.isdigit() else None,
                "time": status
            })

        # winners
        winners = None
        for r in results:
            if r["finish"] == 1:
                winners = r["drivers"]

        race = {
            "year": year,
            "track": "Mount Panorama",
            "results": results,
            "winners": winners
        }

        # SAVE PER YEAR
        file = BASE / f"{year}.json"
        with open(file, "w") as f:
            json.dump(race, f, indent=2)

        print(f"Saved {year}")

        time.sleep(1)

    except Exception as e:
        print("FAILED:", url, e)

print("DONE")
