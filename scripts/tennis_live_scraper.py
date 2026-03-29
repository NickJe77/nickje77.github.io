import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

print("TENNIS LIVE SCRAPER (STABLE VERSION)")

BASE_URL = "https://www.tennisexplorer.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

OUTPUT_DIR = Path("docs/data/tennis/seasons")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2025
END_YEAR = datetime.utcnow().year

session = requests.Session()
session.headers.update(HEADERS)


# -----------------------------------
# SAFE REQUEST (RETRY LOGIC)
# -----------------------------------
def get_soup(url, retries=5):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=20)

            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")

            print(f"Bad status {r.status_code}, retrying...")

        except requests.exceptions.RequestException as e:
            print(f"Request failed ({attempt+1}/{retries}): {e}")

        time.sleep(2 + attempt * 2)  # backoff

    print(f"FAILED URL: {url}")
    return None


# -----------------------------------
# SCRAPE ONE DAY
# -----------------------------------
def scrape_day(date):
    date_str = date.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/matches/?type=all&year={date.year}&month={date.month}&day={date.day}"

    soup = get_soup(url)
    if not soup:
        return []

    matches = []

    rows = soup.select("table.result tbody tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        try:
            tournament = cols[0].get_text(strip=True)
            surface = cols[1].get_text(strip=True)
            round_name = cols[2].get_text(strip=True)
            player1 = cols[3].get_text(strip=True)
            player2 = cols[5].get_text(strip=True)
            score = cols[6].get_text(strip=True)

            if not player1 or not player2:
                continue

            matches.append({
                "date": date_str,
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
# MAIN LOOP
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

        # VERY IMPORTANT (prevents blocking)
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
