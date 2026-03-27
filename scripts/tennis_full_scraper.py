import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import random
import re

print("TENNIS SCRAPER (FINAL — NO TH DEPENDENCY)")

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


def clean_tournament(text):
    text = text.strip()

    text = re.sub(r"\(.*?\)", "", text)

    for s in ["Hard", "Clay", "Grass"]:
        text = text.replace(s, "")

    return text.strip()


def scrape_month(year, month):
    url = f"https://www.tennisexplorer.com/results/atp-men/?year={year}&month={month}"
    print(f"Scraping {year}-{month}")

    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.find_all("tr")

    current_tournament = None
    current_surface = "Hard"

    for row in rows:

        cols = row.find_all("td")

        # -------------------------
        # 🔥 TOURNAMENT ROW DETECTION
        # -------------------------
        if len(cols) == 1:
            txt = cols[0].text.strip()

            if len(txt) > 5:
                print("TOURNAMENT FOUND:", txt)

                current_tournament = clean_tournament(txt)

                low = txt.lower()
                if "clay" in low:
                    current_surface = "Clay"
                elif "grass" in low:
                    current_surface = "Grass"
                else:
                    current_surface = "Hard"

            continue

        # -------------------------
        # MATCH ROW
        # -------------------------
        if len(cols) < 6:
            continue

        try:
            links = row.find_all("a")

            if len(links) < 2:
                continue

            player1 = links[0].text.strip()
            player2 = links[1].text.strip()

            score = cols[-1].text.strip()
            round_val = cols[0].text.strip()

            if not current_tournament:
                continue

            matches.append({
                "tournament": current_tournament,
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


def run():
    all_matches = []

    for year in range(START_YEAR, CURRENT_YEAR + 1):
        max_month = CURRENT_MONTH if year == CURRENT_YEAR else 12

        for month in range(1, max_month + 1):
            all_matches.extend(scrape_month(year, month))
            time.sleep(random.uniform(1, 2))

    print(f"\nTOTAL MATCHES: {len(all_matches)}")

    seasons = {}

    for m in all_matches:
        y = int(m["date"][:4])
        seasons.setdefault(y, []).append(m)

    for y, games in seasons.items():
        with open(MATCH_DIR / f"{y}.json", "w") as f:
            json.dump(games, f, indent=2)

        print(f"Saved {y} ({len(games)})")


run()
