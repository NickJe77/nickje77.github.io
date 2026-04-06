import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("PGA WINNERS BUILDER (API VERSION)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "pga_winners.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

CURRENT_YEAR = datetime.utcnow().year
YEARS = list(range(2015, CURRENT_YEAR + 1))


def get_schedule(year):
    url = f"https://statdata.pgatour.com/r/{year}/schedule-v2.json"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print("Failed schedule", year)
        return []
    return r.json().get("tournaments", [])


def get_leaderboard(tid):
    url = f"https://statdata.pgatour.com/r/{tid}/leaderboard-v2mini.json"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    return r.json()


def get_winner(lb):
    if not lb:
        return None, None

    players = lb.get("players", [])
    if not players:
        return None, None

    p = players[0]

    name = p.get("player_bio", {}).get("full_name", "")
    score = p.get("total", "")

    return name, score


def extract_country(loc):
    if not loc:
        return ""
    return loc.split(",")[-1].strip()


all_rows = []

for year in YEARS:
    print(f"YEAR {year}")

    tournaments = get_schedule(year)

    for t in tournaments:
        try:
            tid = t.get("id")
            name = t.get("name")
            date = t.get("end_date")
            venue = t.get("course_name")
            location = t.get("city_state")

            if not tid or not name:
                continue

            print("  ", name)

            lb = get_leaderboard(tid)
            winner, score = get_winner(lb)

            if not winner:
                continue

            row = {
                "tour": "pga",
                "year": year,
                "date": date,
                "event": name,
                "winner": winner,
                "score": score,
                "venue": venue,
                "country": extract_country(location),
                "url": f"https://www.pgatour.com/tournaments/{year}/{tid}/leaderboard"
            }

            all_rows.append(row)

            time.sleep(0.2)

        except Exception as e:
            print("Error:", e)
            continue


# sort newest first
all_rows.sort(key=lambda x: x.get("date", ""), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(all_rows, f, indent=2)

print("DONE:", len(all_rows))
