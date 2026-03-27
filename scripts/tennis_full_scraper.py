import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import random

print("TENNIS SCRAPER (ALIGNED WITH SITE)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

START_YEAR = 2025
CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().month


def fetch_page(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.text) > 5000:
                return r.text
        except:
            pass

        time.sleep(random.uniform(2, 5))

    return None


def format_date(year, month):
    return f"{year}{str(month).zfill(2)}01"


def scrape_month(year, month):
    url = f"https://www.tennisexplorer.com/results/atp-men/?year={year}&month={month}"
    print(f"Scraping {year}-{month}...")

    html = fetch_page(url)
    if not html:
        print("Failed page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.select("table.result tr")

    current_tournament = "Unknown"

    for r in rows:
        cols = r.find_all("td")

        # detect tournament header rows
        if len(cols) == 1:
            txt = cols[0].text.strip()
            if txt:
                current_tournament = txt
            continue

        if len(cols) < 5:
            continue

        try:
            player1 = cols[2].text.strip()
            player2 = cols[3].text.strip()
            score = cols[4].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "tournament": current_tournament,
                "surface": "Hard",      # temp (we upgrade next)
                "round": "R32",         # temp

                "player1": player1,
                "player2": player2,
                "score": score,

                "date": format_date(year, month),
                "gender": "M"
            })

        except:
            continue

    print(f" → {len(matches)} matches")
    return matches


def run():
    all_matches = []

    for year in range(START_YEAR, CURRENT_YEAR + 1):
        max_month = CURRENT_MONTH if year == CURRENT_YEAR else 12

        for month in range(1, max_month + 1):
            all_matches.extend(scrape_month(year, month))
            time.sleep(random.uniform(1, 3))

    print(f"\nTOTAL: {len(all_matches)} matches")

    # SAVE PER YEAR (FLAT LIST — IMPORTANT)
    seasons = {}

    for m in all_matches:
        year = int(m["date"][:4])
        seasons.setdefault(year, []).append(m)

    for year, games in seasons.items():
        out_file = MATCH_DIR / f"{year}.json"

        with open(out_file, "w") as f:
            json.dump(games, f, indent=2)

        print(f"Saved {len(games)} → {out_file}")


run()
