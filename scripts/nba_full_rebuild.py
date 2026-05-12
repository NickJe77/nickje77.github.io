import os
import json
from glob import glob

INPUT_DIR = "docs/data/nba/boxscores/2026"
OUTPUT_DIR = "docs/data/nba/2026"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("RESTORING NBA 2026 TO OLD FORMAT")

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

files = sorted(glob(f"{INPUT_DIR}/*.json"))

for path in files:

    try:

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        game = raw.get("game", {})

        home = raw.get("homeTeam", {})
        away = raw.get("awayTeam", {})

        output = {
            "game_id": game.get("gameId", ""),
            "date": game.get("gameTimeUTC", ""),
            "game_type": "Regular Season",

            "home_team":
                f"{home.get('teamCity', '')} {home.get('teamName', '')}".strip(),

            "away_team":
                f"{away.get('teamCity', '')} {away.get('teamName', '')}".strip(),

            "home_score": safe_int(home.get("score")),
            "away_score": safe_int(away.get("score")),

            "arena": (
                game.get("arena", {}).get("arenaName", "")
            ),

            "players": []
        }

        for side, team_name in [
            (
                home,
                f"{home.get('teamCity', '')} {home.get('teamName', '')}".strip()
            ),
            (
                away,
                f"{away.get('teamCity', '')} {away.get('teamName', '')}".strip()
            )
        ]:

            players = side.get("players", [])

            if not players:
                players = side.get("gamePlayers", [])

            for p in players:

                stats = (
                    p.get("statistics")
                    or p.get("stats")
                    or {}
                )

                first = (
                    p.get("firstName")
                    or p.get("first_name")
                    or ""
                )

                last = (
                    p.get("familyName")
                    or p.get("lastName")
                    or ""
                )

                full_name = f"{first} {last}".strip()

                if not full_name:
                    full_name = (
                        p.get("name")
                        or p.get("playerName")
                        or "Unknown"
                    )

                output["players"].append({
                    "player": full_name,
                    "team": team_name,

                    "minutes":
                        stats.get("minutes")
                        or stats.get("min")
                        or "0:00",

                    "points":
                        safe_int(
                            stats.get("points")
                            or stats.get("pts")
                        ),

                    "rebounds":
                        safe_int(
                            stats.get("reboundsTotal")
                            or stats.get("rebounds")
                            or stats.get("reb")
                        ),

                    "assists":
                        safe_int(
                            stats.get("assists")
                            or stats.get("ast")
                        ),

                    "steals":
                        safe_int(
                            stats.get("steals")
                            or stats.get("stl")
                        ),

                    "blocks":
                        safe_int(
                            stats.get("blocks")
                            or stats.get("blk")
                        ),

                    "turnovers":
                        safe_int(
                            stats.get("turnovers")
                            or stats.get("tov")
                        )
                })

        out_file = os.path.join(
            OUTPUT_DIR,
            f"{output['game_id']}.json"
        )

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"FIXED {output['game_id']}")

    except Exception as e:

        print(f"FAILED: {path}")
        print(e)

print("DONE")
