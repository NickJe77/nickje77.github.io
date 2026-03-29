import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

print("TENNIS LIVE SCRAPER (WORKING PARSER)")

BASE_URL = "https://www.tennisexplorer.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT_DIR = Path("docs/data/tennis/seasons")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2025
END_YEAR = datetime.utcnow().year

session = requests.Session()
session.headers.update(HEADERS)


# -----------------------------------
# SAFE REQUEST
# -----------------------------------
def get_soup(url, retries=5):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=20)

            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")

        except Exception as e:
            print(f"Retry {attempt+1}: {e}")

        time.sleep(2 + attempt * 2)

    return None


# -----------------------------------
# SCRAPE DAY (FIXED SELECTORS)
# -----------------------------------
def scrape_day(date):
    url = f"{BASE_URL}/matches/?type=all&year={date.year}&month={date.month}&day={date.day}"
    soup = get_soup(url)

    if not soup:
        return []

    matches = []

    # NEW STRUCTURE
    rows = soup.select("tr")

    for row in rows:
        try:
            players = row.select("td.t-name")

            if len(players) < 2:
                continue

            player1 = players[0].get_text(strip=True)
            player2 = players[1].get_text(strip=True)

            score_cell = row.select_one("td.t-score")
            score = score_cell.get_text(strip=True) if score_cell else ""

            round_cell = row.select_one("td.t-round")
            round_name = round_cell.get_text(strip=True) if round_cell else ""

            tournament_cell = row.select_one("td.tournament")
            tournament = tournament_cell.get_text(strip=True) if tournament_cell else ""

            surface_cell = row.select_one("td.surface")
            surface = surface_cell.get_text(strip=True) if surface_cell else ""

            if not player1 or not player2:
                continue

            matches.append({
                "date": date.strftime("%Y-%m-%d"),
                "tournament": tournament,
                "surface": surface,
                "round": round_name,
                "player1": player1,
                "player2": player2,
                "score": score
            })

        except Exception:
            continue

    return matches


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
        print(f"  {d.strftime('%Y-%m-%d')}")

        daily = scrape_day(d)
        all_matches.extend(daily)

        time.sleep(1.5)

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
