import os
import json
from glob import glob

INPUT_DIR = "docs/data/nba/boxscores/2026"
OUTPUT_DIR = "docs/data/nba/2026"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("NORMALIZING NBA 2026 TO OLD FORMAT")

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

files = glob(f"{INPUT_DIR}/*.json")

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
            "home_team": home.get("teamName", ""),
            "away_team": away.get("teamName", ""),
            "home_score": safe_int(home.get("score")),
            "away_score": safe_int(away.get("score")),
            "arena": (
                game.get("arena", {}).get("arenaName", "")
            ),
            "players": []
        }

        for side, team_name in [
            (home, home.get("teamName", "")),
            (away, away.get("teamName", ""))
        ]:

            players = side.get("players", [])

            for p in players:

                stats = p.get("statistics", {})

                output["players"].append({
                    "player": (
                        f"{p.get('firstName', '')} "
                        f"{p.get('familyName', '')}"
                    ).strip(),
                    "team": team_name,
                    "minutes": stats.get("minutes", "0:00"),
                    "points": safe_int(stats.get("points")),
                    "rebounds": safe_int(stats.get("reboundsTotal")),
                    "assists": safe_int(stats.get("assists")),
                    "steals": safe_int(stats.get("steals")),
                    "blocks": safe_int(stats.get("blocks")),
                    "turnovers": safe_int(stats.get("turnovers"))
                })

        out_file = os.path.join(
            OUTPUT_DIR,
            f"{output['game_id']}.json"
        )

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"Fixed {output['game_id']}")

    except Exception as e:
        print(f"FAILED {path}")
        print(e)

print("DONE")
