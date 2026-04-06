import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("PGA WINNERS BUILDER STARTING")

BASE = "https://statdata.pgatour.com/r"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "pga_winners.json"

CURRENT_YEAR = datetime.utcnow().year

# you can extend this back later
YEARS = list(range(2010, CURRENT_YEAR + 1))


def safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None


def get_schedule(year):
    url = f"{BASE}/{year}/schedule-v2.json"
    return safe_get(url)


def get_leaderboard(tournament_id):
    url = f"{BASE}/{tournament_id}/leaderboard-v2mini.json"
    return safe_get(url)


def extract_country(location):
    if not location:
        return ""
    parts = location.split(",")
    return parts[-1].strip()


def extract_winner(leaderboard):
    if not leaderboard:
        return None, None

    players = leaderboard.get("players", [])
    if not players:
        return None, None

    # winner is first place
    winner = players[0]

    name = winner.get("player_bio", {}).get("full_name", "")
    score = winner.get("total", "")

    return name, score


all_results = []

for year in YEARS:
    print(f"Processing {year}...")

    schedule = get_schedule(year)
    if not schedule:
        print(f"Failed schedule {year}")
        continue

    tournaments = schedule.get("tournaments", [])

    for t in tournaments:
        try:
            tid = t.get("id")
            name = t.get("name")
            date = t.get("end_date")
            venue = t.get("course_name")
            location = t.get("city_state")

            if not tid or not name:
                continue

            print(f"  {name}")

            leaderboard = get_leaderboard(tid)

            winner, score = extract_winner(leaderboard)

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

            all_results.append(row)

            time.sleep(0.3)

        except Exception as e:
            print("Error:", e)
            continue


# sort newest first
all_results.sort(key=lambda x: x.get("date", ""), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(all_results, f, indent=2)

print(f"\nDONE - {len(all_results)} tournaments saved")
