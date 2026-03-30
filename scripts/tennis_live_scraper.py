import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

print("TENNIS SCRAPER (FLASHSCORE WORKING)")

OUTPUT_DIR = Path("docs/data/tennis/seasons")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2025
END_YEAR = datetime.utcnow().year

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
})


# -----------------------------------
# FETCH DAY (FLASHSCORE API STYLE)
# -----------------------------------
def fetch_day(date):
    url = f"https://d.flashscore.com/x/feed/f_tn_{date.strftime('%Y%m%d')}"

    try:
        r = session.get(url, timeout=20)

        if r.status_code != 200:
            return []

        text = r.text

        matches = []

        rows = text.split("~")

        for row in rows:
            if "AA÷" not in row:
                continue

            try:
                player1 = row.split("AD÷")[1].split("¬")[0]
                player2 = row.split("AE÷")[1].split("¬")[0]

                score = ""
                if "AG÷" in row:
                    score = row.split("AG÷")[1].split("¬")[0]

                matches.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "player1": player1,
                    "player2": player2,
                    "score": score
                })

            except:
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

        time.sleep(0.5)

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
