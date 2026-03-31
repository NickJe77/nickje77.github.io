import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("MLB 2026 REBUILDER (SAFE)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# GET SCHEDULE
# -------------------------
def get_schedule():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"

    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print("Schedule failed")
        return []

    data = res.json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):

            # ONLY regular + playoffs
            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "id": str(g["gamePk"]),
                "date": g["gameDate"]
            })

    print(f"Found {len(games)} games")
    return games


# -------------------------
# GET BOXSCORE
# -------------------------
def get_boxscore(game_id):
    url = f"{BASE}/game/{game_id}/boxscore"

    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return None

    return res.json()


# -------------------------
# MAIN
# -------------------------
games = get_schedule()

if not games:
    print("NO GAMES FOUND — STOPPING")
    exit()

added = 0
skipped = 0

for g in games:
    game_id = g["id"]
    out_file = BOX_DIR / f"{game_id}.json"

    # DO NOT overwrite existing
    if out_file.exists():
        skipped += 1
        continue

    print(f"Fetching {game_id}")

    data = get_boxscore(game_id)

    if not data:
        print(f"Failed {game_id}")
        continue

    with open(out_file, "w") as f:
        json.dump(data, f)

    added += 1
    time.sleep(0.25)


print(f"\nDONE")
print(f"Added: {added}")
print(f"Skipped (already existed): {skipped}")
