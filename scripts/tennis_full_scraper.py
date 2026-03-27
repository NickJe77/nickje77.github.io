import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import random
import re

print("TENNIS SCRAPER (STABLE FINAL)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 2025
CURRENT_YEAR = datetime.utcnow().year
CURRENT_MONTH = datetime.utcnow().month


# -----------------------------
# FETCH
# -----------------------------
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


# -----------------------------
# CLEAN HEADER
# -----------------------------
def clean_header(text):
    text = text.strip()

    # remove brackets
    text = re.sub(r"\(.*?\)", "", text)

    # remove surfaces
    for s in ["Hard", "Clay", "Grass"]:
        text = text.replace(s, "")

    return text.strip()


# -----------------------------
# SCRAPE MONTH
# -----------------------------
def scrape_month(year, month):
    url = f"https://www.tennisexplorer.com/results/atp-men/?year={year}&month={month}"
    print(f"Scraping {year}-{month}")

    html = fetch(url)
    if not html:
        print("Failed page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.find_all("tr")   # 🔥 robust selector

    current_tournament = "Unknown"
    current_surface = "Hard"

    for row in rows:

        # -------------------------
        # HEADER DETECTION
        # -------------------------
        if row.find("th"):
            txt = row.get_text(strip=True)

            if txt and len(txt) > 5:
                print("HEADER FOUND:", txt)

                current_tournament = clean_header(txt)

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

            score = cols[-1].text.strip()
            round_val = cols[0].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "tournament": current_tournament,   # 🔥 always set
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
# MAIN
# -----------------------------
def run():
    all_matches = []

    for year in range(START_YEAR, CURRENT_YEAR + 1):
        max_month = CURRENT_MONTH if year == CURRENT_YEAR else 12

        for month in range(1, max_month + 1):
            matches = scrape_month(year, month)
            all_matches.extend(matches)

            time.sleep(random.uniform(1, 2))

    print(f"\nTOTAL MATCHES: {len(all_matches)}")

    seasons = {}

    for m in all_matches:
        y = int(m["date"][:4])
        seasons.setdefault(y, []).append(m)

    for y, games in seasons.items():
        out_file = MATCH_DIR / f"{y}.json"

        with open(out_file, "w") as f:
            json.dump(games, f, indent=2)

        print(f"Saved {y} ({len(games)})")


run()
