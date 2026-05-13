import os
import json
from datetime import datetime

BASE_DIR = "docs/data/nba"
SEASON = "2025"
SEASON_DIR = os.path.join(BASE_DIR, SEASON)

OUTPUT_FILE = os.path.join(SEASON_DIR, "index.json")

games = []

print(f"REBUILDING NBA INDEX FOR {SEASON}")
print(f"READING: {SEASON_DIR}")

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

def get_team_name(team_obj):
    if not isinstance(team_obj, dict):
        return ""

    return (
        team_obj.get("teamName")
        or team_obj.get("name")
        or team_obj.get("fullName")
        or team_obj.get("team")
        or ""
    )

for filename in os.listdir(SEASON_DIR):

    if not filename.endswith(".json"):
        continue

    if filename == "index.json":
        continue

    path = os.path.join(SEASON_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:
        print(f"FAILED: {filename} -> {e}")
        continue

    game_pk = (
        data.get("gamePk")
        or data.get("id")
        or filename.replace(".json", "")
    )

    game_date = (
        data.get("gameDate")
        or data.get("date")
        or ""
    )

    try:
        sortable_date = datetime.fromisoformat(
            game_date.replace("Z", "")
        )
    except:
        try:
            sortable_date = datetime.strptime(game_date[:10], "%Y-%m-%d")
        except:
            sortable_date = datetime(1900, 1, 1)

    teams = data.get("teams", {})

    home = teams.get("home", {})
    away = teams.get("away", {})

    home_team = get_team_name(home.get("team", {}))
    away_team = get_team_name(away.get("team", {}))

    home_score = safe_int(home.get("score"))
    away_score = safe_int(away.get("score"))

    winner = home_team if home_score > away_score else away_team

    game_type = (
        data.get("gameType")
        or data.get("type")
        or ""
    )

    if game_type == "R":
        game_type = "Regular Season"

    elif game_type == "P":
        game_type = "Playoffs"

    elif game_type == "F":
        game_type = "Playoffs"

    elif not game_type:
        if "playoff" in json.dumps(data).lower():
            game_type = "Playoffs"
        else:
            game_type = "Regular Season"

    game = {
        "game_id": str(game_pk),
        "game_file": filename,
        "date": sortable_date.strftime("%m/%d/%Y"),
        "timestamp": sortable_date.isoformat(),
        "home_team": home_team,
        "away_team": away_team,
        "game": f"{away_team} vs {home_team}",
        "winner": winner,
        "score": f"{away_score} – {home_score}",
        "type": game_type
    }

    games.append(game)

games.sort(key=lambda x: x["timestamp"])

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(games, f, indent=2)

print()
print("=" * 50)
print(f"REBUILT INDEX")
print(f"GAMES FOUND: {len(games)}")
print(f"SAVED: {OUTPUT_FILE}")
print("=" * 50)
