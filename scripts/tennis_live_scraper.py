import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

print("LIVE TENNIS SCRAPER (REAL FIX)")

BASE = Path("docs/data/tennis")
MATCHES = BASE / "matches"
SEASONS = BASE / "seasons"

MATCHES.mkdir(parents=True, exist_ok=True)
SEASONS.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

YEARS = [2025, 2026]


def slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


def daterange(start, end):
    for n in range((end - start).days + 1):
        yield start + timedelta(n)


def fetch_day(date):
    url = f"https://api.atptour.com/en/scores/current/{date.strftime('%Y-%m-%d')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        return r.json().get("scores", [])
    except:
        return []


def build_match(m):
    try:
        p1 = m["players"][0]["name"]
        p2 = m["players"][1]["name"]
        score = m.get("score", "")
        date = m.get("date", "")

        return {
            "match_id": f"{date}_{slug(p1)}_{slug(p2)}",
            "date": date,
            "tournament": m.get("tournamentName", ""),
            "surface": m.get("surface", ""),
            "round": m.get("round", ""),
            "player1": p1,
            "player2": p2,
            "winner": p1,
            "loser": p2,
            "score": score,
            "gender": "M",
            "best_of": 3,
            "draw_size": 0,
            "minutes": 0,
            "tourney_level": "",
            "tourney_id": ""
        }
    except:
        return None


def scrape_year(year):
    print(f"Scraping {year}")

    start = datetime(year, 1, 1)
    end = datetime.utcnow()

    matches = []

    for d in daterange(start, end):
        daily = fetch_day(d)

        for m in daily:
            built = build_match(m)
            if built:
                matches.append(built)

    return matches


for year in YEARS:
    data = scrape_year(year)

    (MATCHES / f"{year}.json").write_text(json.dumps(data, indent=2))
    (SEASONS / f"{year}.json").write_text(json.dumps(data, indent=2))

    print(f"{year}: {len(data)} matches")

print("DONE")
