import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import random

print("TENNIS FULL SCRAPER (GITHUB SAFE)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

START_YEAR = 2025
CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().month


def fetch_page(url):
    for attempt in range(3):
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)

            if res.status_code == 200 and len(res.text) > 5000:
                return res.text

        except:
            pass

        print(f"Retrying ({attempt+1})...")
        time.sleep(random.uniform(2, 5))

    return None


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

    for r in rows:
        cols = r.find_all("td")

        if len(cols) < 5:
            continue

        try:
            date = cols[0].text.strip()
            player1 = cols[2].text.strip()
            player2 = cols[3].text.strip()
            score = cols[4].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "date": date,
                "player1": player1,
                "player2": player2,
                "score": score,
                "season": year,
                "tournament": "ATP Event",
                "surface": "Hard",
                "round": "R32"
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
            matches = scrape_month(year, month)
            all_matches.extend(matches)

            time.sleep(random.uniform(1, 3))  # 🔥 anti-block

    print(f"\nTOTAL: {len(all_matches)} matches")

    seasons = {}

    for m in all_matches:
        seasons.setdefault(m["season"], []).append(m)

    for season, games in seasons.items():
        out_file = MATCH_DIR / f"{season}.json"

        with open(out_file, "w") as f:
            json.dump({
                "season": season,
                "matches": games
            }, f, indent=2)

        print(f"Saved {len(games)} → {out_file}")


run()
