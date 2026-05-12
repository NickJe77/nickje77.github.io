import os
import json
import requests
from glob import glob

SEASON_DIR = "docs/data/nba/2026"
BOXSCORE_DIR = "docs/data/nba/boxscores/2026"

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(BOXSCORE_DIR, exist_ok=True)

print("NBA 2026 REBUILD STARTED")

schedule_files = sorted(glob(f"{SEASON_DIR}/*.json"))

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

headers = {
    "User-Agent": "Mozilla/5.0"
}

for existing in schedule_files:

    try:

        with open(existing, "r", encoding="utf-8") as f:
            old_game = json.load(f)

        game_id = (
            old_game.get("game_id")
            or old_game.get("gameId")
        )

        if not game_id:
            continue

        print(f"FETCHING {game_id}")

        url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

        res = requests.get(url, headers=headers, timeout=30)

        if res.status_code != 200:
            print(f"FAILED {game_id}")
            continue

        raw = res.json()

        game = raw.get("game", {})

        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})

        home_team = (
            f"{home.get('teamCity', '')} "
            f"{home.get('teamName', '')}"
        ).strip()

        away_team = (
            f"{away.get('teamCity', '')} "
            f"{away.get('teamName', '')}"
        ).strip()

        output = {
            "game_id": game.get("gameId", game_id),
            "date": game.get("gameEt", ""),
            "game_type": "Regular Season",

            "home_team": home_team,
            "away_team": away_team,

            "home_score":
                safe_int(home.get("score")),

            "away_score":
                safe_int(away.get("score")),

            "arena":
                game.get("arena", {}).get("arenaName", ""),

            "players": []
        }

        for side, team_name in [
            (home, home_team),
            (away, away_team)
        ]:

            players = side.get("players", [])

            for p in players:

                stats = p.get("statistics", {})

                first = p.get("firstName", "")
                last = p.get("familyName", "")

                full_name = f"{first} {last}".strip()

                output["players"].append({

                    "player": full_name,
                    "team": team_name,

                    "minutes":
                        stats.get("minutes", "0:00"),

                    "points":
                        safe_int(stats.get("points")),

                    "rebounds":
                        safe_int(stats.get("reboundsTotal")),

                    "assists":
                        safe_int(stats.get("assists")),

                    "steals":
                        safe_int(stats.get("steals")),

                    "blocks":
                        safe_int(stats.get("blocks")),

                    "turnovers":
                        safe_int(stats.get("turnovers"))
                })

        out_file = os.path.join(
            SEASON_DIR,
            f"{game_id}.json"
        )

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"UPDATED {game_id}")

    except Exception as e:

        print(f"ERROR {existing}")
        print(e)

print("NBA 2026 REBUILD COMPLETE")
