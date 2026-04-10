import requests
import json
from pathlib import Path

print("NHL SCORERS BUILDER (FIXED NAMES)")

SEASON = 2026

SEASON_FILE = Path(f"docs/data/nhl/seasons/{SEASON}.json")
BOX_DIR = Path(f"docs/data/nhl/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

def fetch(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        return {}
    return {}

if not SEASON_FILE.exists():
    print("Missing season file")
    exit()

games = json.loads(SEASON_FILE.read_text())

count = 0
MAX_PER_RUN = 200

for game in games:

    game_id = game.get("game_id") or game.get("id")
    file_path = BOX_DIR / f"{game_id}.json"

    if file_path.exists():
        continue

    print(f"Building {game_id}")

    pbp = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play")
    box = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore")

    try:
        # 🔥 BUILD PLAYER MAP
        player_map = {}

        for side in ["homeTeam", "awayTeam"]:
            team = box.get(side, {})
            for p in team.get("players", []):
                pid = p.get("playerId")
                name = p.get("name", {}).get("default")
                if pid and name:
                    player_map[pid] = name

        # 🔥 FIXED PLAY EXTRACTION
        plays = pbp.get("plays") or pbp.get("gameData", {}).get("plays") or []

        goals = []

        for play in plays:
            if play.get("typeDescKey") != "goal":
                continue

            d = play.get("details", {})

            scorer_id = d.get("scoringPlayerId")
            a1 = d.get("assist1PlayerId")
            a2 = d.get("assist2PlayerId")

            goals.append({
                "period": play.get("periodDescriptor", {}).get("number"),
                "time": play.get("timeInPeriod"),
                "scorer": player_map.get(scorer_id),
                "assists": [
                    player_map.get(a) for a in [a1, a2] if player_map.get(a)
                ],
                "strength": d.get("strength")
            })

        game_json = {
            "game_id": game_id,
            "date": game["date"],
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "home_score": game["home_score"],
            "away_score": game["away_score"],
            "goals": goals
        }

        file_path.write_text(json.dumps(game_json, indent=2))

        count += 1
        if count >= MAX_PER_RUN:
            print("Hit limit, stopping")
            break

    except Exception as e:
        print(f"FAILED {game_id}: {e}")
        continue

print("DONE")
