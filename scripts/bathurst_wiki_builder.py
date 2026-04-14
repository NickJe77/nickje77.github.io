import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (WORKING VERSION - TEAM MAP)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2003
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


def clean(v):
    if not v:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def safe_int(v):
    if not v:
        return None
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None


# -----------------------
# GET TEAM → DRIVERS MAP
# -----------------------
def get_team_map(soup):
    team_map = {}

    for table in soup.find_all("table"):
        text = table.get_text(" ").lower()

        if "driver" not in text or "team" not in text:
            continue

        rows = table.find_all("tr")

        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue

            car_no = safe_int(tds[0].get_text())
            if not car_no:
                continue

            d1 = clean(tds[2].get_text())
            d2 = clean(tds[3].get_text())

            drivers = []
            for d in [d1, d2]:
                if d and len(d.split()) >= 2:
                    drivers.append(d)

            if drivers:
                team_map[car_no] = drivers

        if team_map:
            return team_map

    return {}


# -----------------------
# GET RESULTS TABLE
# -----------------------
def get_results(soup, team_map):
    best = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if len(rows) < 8:
            continue

        header = rows[0].get_text(" ").lower()

        if "pos" not in header:
            continue

        results = []

        for tr in rows[1:]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue

            pos = safe_int(tds[0].get_text())
            if pos is None:
                continue

            car_no = safe_int(tds[1].get_text())

            drivers = team_map.get(car_no, [])

            constructor = None
            if len(tds) > 4:
                constructor = clean(tds[4].get_text())

            results.append({
                "finish_pos": pos,
                "drivers": drivers,
                "constructor": constructor
            })

        if len(results) > len(best):
            best = results

    return best


# -----------------------
# MAIN
# -----------------------
def scrape_year(year):
    url = "https://en.wikipedia.org/wiki/" + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    team_map = get_team_map(soup)

    results = get_results(soup, team_map)

    if not results:
        return None

    results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"],
        "source": url
    }


# -----------------------
# RUN
# -----------------------
for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    file_path = SEASONS_DIR / f"{year}.json"

    data = scrape_year(year)

    if not data:
        print("FAILED — keeping existing")
        continue

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"saved {len(data['results'])} rows")

    time.sleep(0.2)

print("\nDONE")
