import os
import json
import requests
import time

NBA_DIR = "docs/data/nba/2025"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/"
}

print("NBA EXACT SCHEMA IMPORTER")

os.makedirs(NBA_DIR, exist_ok=True)

def safe_int(v):
    try:
        return int(v)
    except:
        try:
            return int(float(v))
        except:
            return 0

# =========================================================
# ALL PLAYOFF GAME IDS
# =========================================================

PLAYOFF_IDS = [

    # ROUND 1
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
    "0042400407",

    # ROUND 2
    "0042400211",
    "0042400212",
    "0042400213",
    "0042400214",
    "0042400215",
    "0042400216",
    "0042400217",

    "0042400221",
    "0042400222",
    "0042400223",
    "0042400224",
    "0042400225",
    "0042400226",
    "0042400227",

    "0042400231",
    "0042400232",
    "0042400233",
    "0042400234",
    "0042400235",
    "0042400236",
    "0042400237",

    "0042400241",
    "0042400242",
    "0042400243",
    "0042400244",
    "0042400245",
    "0042400246",
    "0042400247",

    # CONFERENCE FINALS
    "0042400311",
    "0042400312",
    "0042400313",
    "0042400314",
    "0042400315",
    "0042400316",
    "0042400317",

    "0042400321",
    "0042400322",
    "0042400323",
    "0042400324",
    "0042400325",
    "0042400326",
    "0042400327",

    # NBA FINALS
    "0042400401",
    "0042400402",
    "0042400403",
    "0042400404",
    "0042400405",
    "0042400406",
    "0042400407"
]

# remove duplicates while preserving order
PLAYOFF_IDS = list(dict.fromkeys(PLAYOFF_IDS))

# =========================================================
# IMPORT LOOP
# =========================================================

for game_id in PLAYOFF_IDS:

    try:

        out_path = os.path.join(
            NBA_DIR,
            f"{game_id}.json"
        )

        # =================================================
        # SKIP IF ALREADY GOOD
        # =================================================

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

        # =================================================
        # EXACT WORKING SCHEMA
        # =================================================

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

        # =================================================
        # HOME + AWAY PLAYERS
        # =================================================

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

        # =================================================
        # SAVE
        # =================================================

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

        time.sleep(1)

    except Exception as e:

        print(f"FAILED {game_id}")
        print(str(e))

print("DONE")
