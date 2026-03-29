import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

print("TENNIS LIVE SCRAPER (XHR VERSION - WORKING)")

BASE = "https://www.tennisexplorer.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.tennisexplorer.com/matches/"
}

OUTPUT_DIR = Path("docs/data/tennis/seasons")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2025
END_YEAR = datetime.utcnow().year

session = requests.Session()
session.headers.update(HEADERS)


# -----------------------------------
# GET MATCHES VIA XHR
# -----------------------------------
def fetch_day(date):
    url = f"{BASE}/matches/?type=all&year={date.year}&month={date.month}&day={date.day}"

    try:
        r = session.get(url, timeout=20)

        if r.status_code != 200:
            return []

        html = r.text

        matches = []

        # crude but reliable parsing (XHR returns clean rows)
        rows = html.split('<tr')

        for row in rows:
            if 't-name' not in row:
                continue

            try:
                parts = row.split('t-name')

                p1 = parts[1].split('>')[1].split('<')[0].strip()
                p2 = parts[2].split('>')[1].split('<')[0].strip()

                score = ""
                if 't-score' in row:
                    score = row.split('t-score')[1].split('>')[1].split('<')[0].strip()

                round_name = ""
                if 't-round' in row:
                    round_name = row.split('t-round')[1].split('>')[1].split('<')[0].strip()

                matches.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "player1": p1,
                    "player2": p2,
                    "score": score,
                    "round": round_name
                })

            except Exception:
                continue

        return matches

    except Exception as e:
        print("FAILED:", e)
        return []


# -----------------------------------
# YEAR LOOP
# -----------------------------------
def scrape_year(year):
    print(f"\nScraping {year}...")

    start = datetime(year, 1, 1)
    end = datetime.utcnow() if year == END_YEAR else datetime(year, 12, 31)

    all_matches = []

    d = start
    while d <= end:
        print(d.strftime("%Y-%m-%d"))

        daily = fetch_day(d)
        all_matches.extend(daily)

        time.sleep(1)  # keep safe

        d += timedelta(days=1)

    print(f"{year} matches: {len(all_matches)}")

    if all_matches:
        with open(OUTPUT_DIR / f"{year}.json", "w") as f:
            json.dump(all_matches, f, indent=2)

    return len(all_matches)


# -----------------------------------
# RUN
# -----------------------------------
total = 0

for y in range(START_YEAR, END_YEAR + 1):
    total += scrape_year(y)

print(f"\nDONE. TOTAL MATCHES: {total}")
