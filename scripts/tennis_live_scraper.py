import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

OUTPUT = "docs/data/tennis/matches"
os.makedirs(OUTPUT, exist_ok=True)

CURRENT_YEAR = datetime.now().year
YEARS = list(range(2025, CURRENT_YEAR + 1))

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

DELAY = 1.5


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
# GET TOURNAMENTS
# =========================
def get_tournaments(year):
    url = f"https://www.atptour.com/en/scores/results-archive?year={year}"

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    tournaments = set()

    for a in soup.select("a"):
        href = a.get("href", "")
        if "/scores/archive/" in href and f"/{year}/" in href:
            if "results" in href:
                tournaments.add("https://www.atptour.com" + href)

    return list(tournaments)


# =========================
# 🔥 REAL MATCH EXTRACTION
# =========================
def get_matches(tournament_url):
    res = requests.get(tournament_url, headers=HEADERS)
    html = res.text

    matches = []

    try:
        # 🔥 FIND EMBEDDED JSON
        script_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html)

        if not script_match:
            return []

        data = json.loads(script_match.group(1))

        # navigate structure (ATP changes this often)
        draws = data.get("scores", {}).get("draws", [])

        for draw in draws:
            for match in draw.get("matches", []):
                try:
                    p1 = match.get("player1", {}).get("name", "")
                    p2 = match.get("player2", {}).get("name", "")
                    score = match.get("score", "")

                    if p1 and p2:
                        matches.append({
                            "player1": p1,
                            "player2": p2,
                            "score": score,
                            "tournament_url": tournament_url
                        })

                except:
                    continue

    except Exception as e:
        print("PARSE FAIL:", e)

    return matches


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

            matches = get_matches(t)

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
