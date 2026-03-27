import requests
import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

CURRENT_YEAR = datetime.now().year
YEARS = list(range(2025, CURRENT_YEAR + 1))

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

DELAY = 1


# =========================
# LOAD / SAVE
# =========================
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


# =========================
# GET TOURNAMENT LINKS
# =========================
def get_tournaments(year):
    url = f"https://www.atptour.com/en/scores/results-archive?year={year}"

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    tournaments = []

    for a in soup.select("a"):
        href = a.get("href", "")
        if "/scores/archive/" in href and f"/{year}/" in href:
            full = "https://www.atptour.com" + href
            if "results" in full:
                tournaments.append(full)

    return list(set(tournaments))


# =========================
# 🔥 REAL MATCH FETCHER (API)
# =========================
def get_matches_api(tournament_url):
    try:
        parts = tournament_url.split("/")

        # Example:
        # /archive/indian-wells/404/2026/results
        slug = parts[-5]
        tourney_id = parts[-4]
        year = parts[-3]

        api_url = f"https://www.atptour.com/-/api/scores/archive/{slug}/{tourney_id}/{year}"

        res = requests.get(api_url, headers=HEADERS)

        if res.status_code != 200:
            return []

        data = res.json()

        matches = []

        for match in data.get("matches", []):
            try:
                p1 = match.get("player1", {}).get("name", "")
                p2 = match.get("player2", {}).get("name", "")
                score = match.get("score", "")

                if p1 and p2:
                    matches.append({
                        "player1": p1,
                        "player2": p2,
                        "score": score,
                        "tournament": slug,
                        "year": int(year)
                    })

            except:
                continue

        return matches

    except:
        return []


# =========================
# MAIN
# =========================
def run():
    for year in YEARS:
        print(f"\nYEAR: {year}")

        existing = load_existing(year)
        seen = {(m["player1"], m["player2"], m["score"]) for m in existing}

        tournaments = get_tournaments(year)

        print(f"Found {len(tournaments)} tournaments")

        new_matches = []

        for t in tournaments:
            print("SCRAPING:", t)

            matches = get_matches_api(t)

            added = 0

            for m in matches:
                key = (m["player1"], m["player2"], m["score"])
                if key not in seen:
                    new_matches.append(m)
                    seen.add(key)
                    added += 1

            print(f"  + {added} new matches")

            time.sleep(DELAY)

        all_matches = existing + new_matches

        save_year(year, all_matches)

        print(f"Saved {len(all_matches)} matches ({len(new_matches)} new)")


if __name__ == "__main__":
    run()
