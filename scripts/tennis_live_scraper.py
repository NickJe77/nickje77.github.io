import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

# ==============================
# CONFIG
# ==============================
OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

CURRENT_YEAR = datetime.now().year
YEARS = list(range(2025, CURRENT_YEAR + 1))

BASE_URL = "https://www.atptour.com/en/scores/results-archive"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

DELAY = 1.5  # be nice, avoid blocks


# ==============================
# HELPERS
# ==============================
def load_existing(year):
    path = f"{OUTPUT}/{year}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_year(year, data):
    path = f"{OUTPUT}/{year}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_tournaments(year):
    print(f"Fetching tournaments for {year}")
    url = f"{BASE_URL}?year={year}"

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    tournaments = []

    for row in soup.select("tr.tourney-result"):
        link = row.select_one("a")
        if not link:
            continue

        href = link.get("href")
        if not href:
            continue

        full_url = "https://www.atptour.com" + href

        tournaments.append(full_url)

    print(f"Found {len(tournaments)} tournaments")
    return tournaments


def get_matches(tournament_url):
    res = requests.get(tournament_url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    matches = []

    for match in soup.select(".day-table tr"):
        players = match.select(".day-table-name")
        score = match.select_one(".day-table-score")

        if len(players) < 2 or not score:
            continue

        p1 = players[0].get_text(strip=True)
        p2 = players[1].get_text(strip=True)
        sc = score.get_text(strip=True)

        matches.append({
            "player1": p1,
            "player2": p2,
            "score": sc,
            "tournament_url": tournament_url
        })

    return matches


# ==============================
# MAIN RUNNER
# ==============================
def run():
    for year in YEARS:
        print(f"\n====================")
        print(f"YEAR: {year}")
        print(f"====================")

        existing = load_existing(year)

        # Track already scraped tournaments
        done_tournaments = set()
        for m in existing:
            if "tournament_url" in m:
                done_tournaments.add(m["tournament_url"])

        print(f"Already have {len(existing)} matches")
        print(f"Already scraped {len(done_tournaments)} tournaments")

        tournaments = get_tournaments(year)

        new_matches = []

        for t in tournaments:
            if t in done_tournaments:
                print("SKIP:", t)
                continue

            print("SCRAPING:", t)

            try:
                matches = get_matches(t)

                if matches:
                    new_matches.extend(matches)
                    print(f"  + {len(matches)} matches")
                else:
                    print("  (no matches found)")

                time.sleep(DELAY)

            except Exception as e:
                print("FAILED:", t, e)

        all_matches = existing + new_matches

        save_year(year, all_matches)

        print(f"\nSaved {len(all_matches)} total matches for {year}")
        print(f"New matches added: {len(new_matches)}")


# ==============================
# ENTRY
# ==============================
if __name__ == "__main__":
    run()
