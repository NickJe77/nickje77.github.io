import requests
import json
from pathlib import Path
import time

print("MLB BOXSCORE BUILDER")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")
OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

games = json.load(open(SEASON_FILE))


def get_box(game_id):
    url = f"{BASE}/game/{game_id}/boxscore"
    r = requests.get(url)

    try:
        data = r.json()
    except:
        return None

    if "teams" not in data:
        return None

    return data


for g in games:
    gid = g["game_id"]

    if g["status"] != "Final":
        continue

    out = OUT_DIR / f"{gid}.json"

    print("Processing", gid)

    box = get_box(gid)

    if not box:
        print("FAILED", gid)
        continue

    with open(out, "w") as f:
        json.dump(box, f, indent=2)

    time.sleep(0.4)
