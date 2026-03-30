import json
from pathlib import Path

SEASON = "2026"

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")

print("FIXING 2026 BOXSCORES → MATCHING OLD FORMAT")

# -------------------------
# LOAD SEASON (for teams)
# -------------------------
season_data = json.loads(SEASON_FILE.read_text())

games = season_data["games"] if isinstance(season_data, dict) else season_data

game_lookup = {str(g["game_id"]): g for g in games}

# -------------------------
# PROCESS EACH GAME
# -------------------------
for file in BOX_DIR.glob("*.json"):

    game_id = file.stem

    if game_id not in game_lookup:
        print(f"Skipping {game_id} (not in season file)")
        continue

    meta = game_lookup[game_id]

    away_team = meta["away_team"]
    home_team = meta["home_team"]

    data = json.loads(file.read_text())

    # -------------------------
    # SKIP IF ALREADY FIXED
    # -------------------------
    if isinstance(data, dict) and "batters_away" in data:
        continue

    if not isinstance(data, list):
        print(f"Skipping {game_id} (unexpected format)")
        continue

    # -------------------------
    # SPLIT PLAYERS
    # -------------------------
    away_players = []
    home_players = []

    for p in data:

        player_obj = {
            "player": p.get("player"),
            "hits": p.get("hits"),
            "runs": p.get("runs"),
            "rbi": p.get("rbi"),
            "home_runs": p.get("home_runs")
        }

        if p.get("team") == away_team:
            away_players.append(player_obj)

        elif p.get("team") == home_team:
            home_players.append(player_obj)

    # -------------------------
    # BUILD NEW STRUCTURE
    # -------------------------
    new_data = {
        "batters_away": away_players,
        "batters_home": home_players,
        "pitchers_away": [],
        "pitchers_home": []
    }

    # -------------------------
    # SAVE
    # -------------------------
    file.write_text(json.dumps(new_data, indent=2))

    print(f"✔ Fixed {game_id}")

print("DONE")
