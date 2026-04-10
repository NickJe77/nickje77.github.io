import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST SCRAPER (1963+)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2026


def clean(text):
    text = re.sub(r"\[\d+\]", "", text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_drivers(cell):
    lines = cell.get_text("\n", strip=True).split("\n")

    drivers = []
    for l in lines:
        l = clean(l)

        # skip junk
        if not l:
            continue
        if re.fullmatch(r"\d+", l):
            continue
        if l.lower() in ["australia", "new zealand", "uk", "usa"]:
            continue

        drivers.append(l)

    # remove duplicates
    seen = set()
    final = []
    for d in drivers:
        if d not in seen:
            seen.add(d)
            final.append(d)

    return final


for year in range(START_YEAR, END_YEAR + 1):

    try:
        url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"
        print(f"Scraping {year}")

        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            print(f"Skip {year}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        tables = soup.select("table.wikitable")

        table = None
        for t in tables:
            head = t.get_text(" ", strip=True).lower()
            if "drivers" in head and "car" in head:
                table = t
                break

        if not table:
            print(f"No table {year}")
            continue

        results = []

        rows = table.find_all("tr")[1:]

        for r in rows:
            cols = r.find_all("td")

            if len(cols) < 5:
                continue

            finish_text = clean(cols[0].get_text())

            if not re.match(r"^\d+$", finish_text):
                continue

            finish = int(finish_text)

            drivers = extract_drivers(cols[3])
            car = clean(cols[4].get_text())

            laps = None
            if len(cols) > 5:
                m = re.search(r"\d+", cols[5].get_text())
                if m:
                    laps = int(m.group())

            results.append({
                "finish": finish,
                "grid": None,
                "drivers": drivers,
                "car": car,
                "laps": laps,
                "time": None
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
        print(f"FAILED {year}: {e}")

print("DONE")
