import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FIXED TEAM MAP)")

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
# TEAM → DRIVERS MAP (FIXED)
# -----------------------
def get_team_map(soup):
    team_map = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        header = rows[0].get_text(" ").lower()

        # must be teams table
        if "driver" not in header or "team" not in header:
            continue

        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            car_no = safe_int(cells[0].get_text())
            if not car_no:
                continue

            # 🔥 GET ALL DRIVER NAMES FROM ROW
            names = []

            for a in tr.find_all("a"):
                name = clean(a.get_text())
                if name and len(name.split()) >= 2:
                    names.append(name)

            # fallback if no <a>
            if not names:
                text = tr.get_text("\n")
                parts = re.split(r"\n|/|,|&| and ", text)

                for p in parts:
                    p = clean(p)
                    if p and len(p.split()) >= 2:
                        names.append(p)

            # dedupe
            seen = set()
            drivers = []
            for n in names:
                k = n.lower()
                if k not in seen:
                    drivers.append(n)
                    seen.add(k)

            if drivers:
                team_map[car_no] = drivers

        if team_map:
            return team_map

    return {}


# -----------------------
# RESULTS TABLE
# -----------------------
def get_results(soup, team_map):
    best = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if len(rows) < 5:
            continue

        header = rows[0].get_text(" ").lower()

        if "pos" not in header:
            continue

        results = []

        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            pos = safe_int(cells[0].get_text())
            if pos is None:
                continue

            car_no = safe_int(cells[1].get_text())

            drivers = team_map.get(car_no, [])

            constructor = None
            if len(cells) > 4:
                constructor = clean(cells[4].get_text())

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

    print(f"  team map entries: {len(team_map)}")

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
