import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("TENNIS FULL SCRAPER (PLAYER-BASED — RELIABLE)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔥 START WITH KNOWN PLAYER LIST (we expand later)
PLAYERS = [
    "novak-djokovic",
    "carlos-alcaraz",
    "jannik-sinner",
    "daniil-medvedev",
    "alexander-zverev",
    "stefanos-tsitsipas",
    "andrey-rublev",
    "casper-ruud",
    "holger-rune",
    "taylor-fritz"
]

BASE_URL = "https://www.tennisexplorer.com/player/{}/?matches=1"


def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
    except:
        return None


def parse_player(player_slug):
    url = BASE_URL.format(player_slug)
    print(f"Fetching {player_slug}")

    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    rows = soup.select("table.result tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 6:
            continue

        try:
            date = cols[0].text.strip().replace(".", "")
            opponent = cols[2].text.strip()
            score = cols[3].text.strip()
            tournament = cols[1].text.strip()

            if not opponent:
                continue

            matches.append({
                "tournament": tournament,
                "surface": "Hard",   # upgrade later
                "round": "R32",

                "player1": player_slug.replace("-", " ").title(),
                "player2": opponent,
                "score": score,

                "date": date,
                "gender": "M"
            })

        except:
            continue

    print(f" → {len(matches)} matches")
    return matches


def run():
    all_matches = []

    for p in PLAYERS:
        matches = parse_player(p)
        all_matches.extend(matches)
        time.sleep(1)

    print(f"\nTOTAL MATCHES: {len(all_matches)}")

    # 🔥 FILTER LAST 2 YEARS
    filtered = []
    for m in all_matches:
        try:
            year = int(m["date"][:4])
            if year >= 2025:
                filtered.append(m)
        except:
            continue

    print(f"Filtered: {len(filtered)} matches (2025+)")

    seasons = {}

    for m in filtered:
        y = int(m["date"][:4])
        seasons.setdefault(y, []).append(m)

    for y, games in seasons.items():
        with open(MATCH_DIR / f"{y}.json", "w") as f:
            json.dump(games, f, indent=2)

        print(f"Saved {y} ({len(games)})")


run()
