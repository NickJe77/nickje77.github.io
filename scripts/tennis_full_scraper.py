import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import random

print("TENNIS SCRAPER (TOURNAMENT FIXED)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 2025
CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().month


def fetch(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.text
        except:
            pass
        time.sleep(random.uniform(2, 5))
    return None


def scrape_month(year, month):
    url = f"https://www.tennisexplorer.com/results/atp-men/?year={year}&month={month}"
    print(f"Scraping {year}-{month}")

    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.select("table.result tr")

    for row in rows:
        cols = row.find_all("td")

        # skip invalid rows
        if len(cols) < 7:
            continue

        try:
            # 🔥 TOURNAMENT IS IN COLUMN 1 (NOT HEADER)
            tournament = cols[1].text.strip()

            player_links = row.find_all("a")
            if len(player_links) < 2:
                continue

            player1 = player_links[0].text.strip()
            player2 = player_links[1].text.strip()

            score = cols[-1].text.strip()
            round_val = cols[0].text.strip()

            if not tournament or not player1 or not player2:
                continue

            matches.append({
                "tournament": tournament,
                "surface": "Hard",  # temp
                "round": round_val,

                "player1": player1,
                "player2": player2,
                "score": score,

                "date": f"{year}{str(month).zfill(2)}01",
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
            time.sleep(random.uniform(1, 2))

    print(f"\nTOTAL: {len(all_matches)} matches")

    seasons = {}

    for m in all_matches:
        y = int(m["date"][:4])
        seasons.setdefault(y, []).append(m)

    for y, games in seasons.items():
        with open(MATCH_DIR / f"{y}.json", "w") as f:
            json.dump(games, f, indent=2)

        print(f"Saved {y} ({len(games)})")


run()
