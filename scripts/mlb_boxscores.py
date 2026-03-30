import requests
import json
from pathlib import Path
import time

print("MLB BOXSCORE BUILDER (FULL SCRIPT)")

# -------------------------
# CONFIG
# -------------------------
SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")
BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------
# LOAD SEASON DATA
# -------------------------
if not SEASON_FILE.exists():
    print("❌ Season file missing")
    exit()

with open(SEASON_FILE) as f:
    season_data = json.load(f)

games = season_data.get("games", [])

print(f"Loaded {len(games)} games")


# -------------------------
# GET BOXSCORE
# -------------------------
def fetch_boxscore(game_id):
    url = f"{BASE}/game/{game_id}/boxscore"

    try:
        r = requests.get(url, headers=HEADERS)
        data = r.json()
    except Exception as e:
        print("Request failed:", e)
        return None

    if "teams" not in data:
        return None

    return data


# -------------------------
# BUILD GAME OBJECT
# -------------------------
def build_game(game_id, data):
    game = {
        "game_id": game_id,
        "score": {
            "home": {},
            "away": {}
        },
        "players": []
    }

    for side in ["home", "away"]:
        team = data["teams"][side]
        team_name = team["team"]["name"]

        # TEAM SCORE
        game["score"][side] = {
            "team": team_name,
            "runs": team.get("teamStats", {}).get("batting", {}).get("runs", 0),
            "hits": team.get("teamStats", {}).get("batting", {}).get("hits", 0),
            "errors": team.get("teamStats", {}).get("fielding", {}).get("errors", 0)
        }

        # PLAYERS
        for player_id, p in team.get("players", {}).items():

            person = p.get("person", {})
            stats = p.get("stats", {})

            player = {
                "player_id": person.get("id"),
                "name": person.get("fullName"),
                "team": team_name,
                "position": p.get("position", {}).get("abbreviation"),

                "batting": stats.get("batting", {}),
                "pitching": stats.get("pitching", {}),
                "fielding": stats.get("fielding", {})
            }

            game["players"].append(player)

    return game


# -------------------------
# MAIN LOOP
# -------------------------
saved = 0
failed = 0

for g in games:
    game_id = g["game_id"]
    status = g.get("status", "")

    # ONLY FINAL GAMES
    if status != "Final":
        continue

    outfile = BOX_DIR / f"{game_id}.json"

    print(f"Processing {game_id}")

    raw = fetch_boxscore(game_id)

    if not raw:
        print("❌ Failed:", game_id)
        failed += 1
        continue

    game_data = build_game(game_id, raw)

    with open(outfile, "w") as f:
        json.dump(game_data, f, indent=2)

    saved += 1

    time.sleep(0.4)


# -------------------------
# SUMMARY
# -------------------------
print("\nDONE")
print(f"Saved: {saved}")
print(f"Failed: {failed}")
