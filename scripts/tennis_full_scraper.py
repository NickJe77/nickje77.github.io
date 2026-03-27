import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import random

print("TENNIS SCRAPER (FINAL — EVENTS FIXED)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

START_YEAR = 2025
CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().month


# -----------------------------
# FETCH WITH RETRIES
# -----------------------------
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


# -----------------------------
# SCRAPE MONTH
# -----------------------------
def scrape_month(year, month):
    url = f"https://www.tennisexplorer.com/results/atp-men/?year={year}&month={month}"
    print(f"Scraping {year}-{month}")

    html = fetch_page(url)
    if not html:
        print("Failed page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.select("table.result tr")

    current_tournament = None
    current_surface = "Hard"

    for row in rows:

        # 🔥 TOURNAMENT HEADER
        header = row.find("th")
        if header:
            txt = header.text.strip()

            if txt:
                current_tournament = txt

                # surface detection
                low = txt.lower()
                if "clay" in low:
                    current_surface = "Clay"
                elif "grass" in low:
                    current_surface = "Grass"
                else:
                    current_surface = "Hard"

            continue

        cols = row.find_all("td")

        if len(cols) < 6:
            continue

        try:
            links = row.find_all("a")

            if len(links) < 2:
                continue

            player1 = links[0].text.strip()
            player2 = links[1].text.strip()

            round_val = cols[0].text.strip()
            score = cols[-1].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "tournament": current_tournament or "Unknown",
                "surface": current_surface,
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


# -----------------------------
# MAIN RUN
# -----------------------------
def run():
    all_matches = []

    for year in range(START_YEAR, CURRENT_YEAR + 1):
        max_month = CURRENT_MONTH if year == CURRENT_YEAR else 12

        for month in range(1, max_month + 1):
            matches = scrape_month(year, month)
            all_matches.extend(matches)

            time.sleep(random.uniform(1, 3))

    print(f"\nTOTAL MATCHES: {len(all_matches)}")

    # 🔥 SAVE PER YEAR (FLAT LIST — MATCHES YOUR SITE)
    seasons = {}

    for m in all_matches:
        year = int(m["date"][:4])
        seasons.setdefault(year, []).append(m)

    for year, games in seasons.items():
        out_file = MATCH_DIR / f"{year}.json"

        with open(out_file, "w") as f:
            json.dump(games, f, indent=2)

        print(f"Saved {year} ({len(games)})")


run()
