import os
import json
import requests

NBA_DIR = "docs/data/nba/2025"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/"
}

print("NBA EXACT SCHEMA IMPORTER")

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

PLAYOFF_IDS = [

    "0042400101",
    "0042400102",
    "0042400103",
    "0042400104",
    "0042400105",
    "0042400106",
    "0042400107",

    "0042400201",
    "0042400202",
    "0042400203",
    "0042400204",
    "0042400205",
    "0042400206",
    "0042400207",

    "0042400301",
    "0042400302",
    "0042400303",
    "0042400304",
    "0042400305",
    "0042400306",
    "0042400307",

    "0042400401",
    "0042400402",
    "0042400403",
    "0042400404",
    "0042400405",
    "0042400406",
    "0042400407"
]

for game_id in PLAYOFF_IDS:

    try:

        out_path = os.path.join(
            NBA_DIR,
            f"{game_id}.json"
        )

        if os.path.exists(out_path):

            try:

                with open(
                    out_path,
                    "r",
                    encoding="utf-8"
                ) as ef:

                    existing = json.load(ef)

                if (
                    existing.get("players")
                    and existing.get("home_team")
                    and existing.get("away_team")
                ):

                    print(f"SKIP GOOD {game_id}")
                    continue

            except:
                pass

        print(f"IMPORTING {game_id}")

        url = (
            "https://cdn.nba.com/static/json/liveData/"
            f"boxscore/boxscore_{game_id}.json"
        )

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        if r.status_code != 200:

            print(f"BAD BOX {game_id}")
            continue

        raw = r.json()

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

            "game_id": game_id,

            "date":
                game.get("gameEt")
                or game.get("gameTimeUTC")
                or "",

            "game_type": "Playoffs",

            "home_team": home_team,
            "away_team": away_team,

            "home_score":
                safe_int(home.get("score")),

            "away_score":
                safe_int(away.get("score")),

            "arena":
                game.get("arena", {})
                .get("arenaName", ""),

            "players": []
        }

        for side, team_name in [
            (home, home_team),
            (away, away_team)
        ]:

            for p in side.get("players", []):

                stats = p.get(
                    "statistics",
                    {}
                )

                full_name = (
                    f"{p.get('firstName', '')} "
                    f"{p.get('familyName', '')}"
                ).strip()

                if not full_name:
                    continue

                output["players"].append({

                    # EXACT WORKING SCHEMA

                    "player": full_name,

                    "team": team_name,

                    "minutes":
                        stats.get(
                            "minutesCalculated",
                            "0:00"
                        ),

                    "points":
                        safe_int(
                            stats.get("points")
                        ),

                    "rebounds":
                        safe_int(
                            stats.get(
                                "reboundsTotal"
                            )
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

        with open(
            out_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                output,
                f,
                indent=2
            )

        print(f"DONE {game_id}")

    except Exception as e:

        print(f"FAILED {game_id}")
        print(str(e))

print("DONE")
