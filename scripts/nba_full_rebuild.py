import os
import json
import requests
from glob import glob

NBA_DIR = "docs/data/nba/2026"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("FIXING NBA 2026 FILES")

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

files = sorted(glob(f"{NBA_DIR}/*.json"))

for path in files:

    try:

        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)

        game_id = (
            existing.get("game_id")
            or existing.get("gameId")
        )

        if not game_id:
            print(f"NO GAME ID: {path}")
            continue

        print(f"FETCHING {game_id}")

        url = (
            "https://cdn.nba.com/static/json/liveData/"
            f"boxscore/boxscore_{game_id}.json"
        )

        r = requests.get(
            url,
            headers=headers,
            timeout=60
        )

        if r.status_code != 200:
            print(f"BAD STATUS {game_id}")
            continue

        raw = r.json()

        # CORRECT STRUCTURE
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

        fixed = {
            "game_id": game_id,

            "date":
                game.get("gameEt")
                or game.get("gameTimeUTC")
                or "",

            "home_team": home_team,
            "away_team": away_team,

            "home_score":
                safe_int(home.get("score")),

            "away_score":
                safe_int(away.get("score")),

            "arena":
                game.get("arena", {}).get("arenaName", ""),

            "attendance":
                safe_int(game.get("attendance")),

            "players": []
        }

        for side, team_name in [
            (home, home_team),
            (away, away_team)
        ]:

            players = side.get("players", [])

            for p in players:

                if p.get("played") != "1":
                    continue

                stats = p.get("statistics", {})

                full_name = (
                    f"{p.get('firstName', '')} "
                    f"{p.get('familyName', '')}"
                ).strip()

                fixed["players"].append({

                    "player": full_name,
                    "team": team_name,

                    "minutes":
                        stats.get("minutesCalculated", ""),

                    "points":
                        safe_int(stats.get("points")),

                    "rebounds":
                        safe_int(
                            stats.get("reboundsTotal")
                        ),

                    "assists":
                        safe_int(
                            stats.get("assists")
                        ),

                    "steals":
                        safe_int(
                            stats.get("steals")
                        ),

                    "blocks":
                        safe_int(
                            stats.get("blocks")
                        ),

                    "turnovers":
                        safe_int(
                            stats.get("turnovers")
                        )
                })

        with open(path, "w", encoding="utf-8") as f:
            json.dump(fixed, f, indent=2)

        print(f"FIXED {game_id}")

    except Exception as e:

        print(f"FAILED {path}")
        print(str(e))

print("DONE")
