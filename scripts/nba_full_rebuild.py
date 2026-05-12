import os
import json
import requests

NBA_DIR = "docs/data/nba/2025"
PLAYERS_DIR = "docs/data/nba/players"

os.makedirs(NBA_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/"
}

print("NBA PLAYOFF IMPORTER")

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

        existing_path = os.path.join(
            NBA_DIR,
            f"{game_id}.json"
        )

        if os.path.exists(existing_path):

            try:

                with open(
                    existing_path,
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

        print(f"ADDING {game_id}")

        box_url = (
            "https://cdn.nba.com/static/json/liveData/"
            f"boxscore/boxscore_{game_id}.json"
        )

        r = requests.get(
            box_url,
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

            "attendance":
                safe_int(
                    game.get("attendance")
                ),

            "players": []
        }

        for side, team_name in [
            (home, home_team),
            (away, away_team)
        ]:

            for p in side.get("players", []):

                if p.get("played") != "1":
                    continue

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
                            ""
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
            existing_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                output,
                f,
                indent=2
            )

        print(f"ADDED {game_id}")

    except Exception as e:

        print(f"FAILED {game_id}")
        print(str(e))

# BUILD PLAYERS.JSON

print("BUILDING PLAYERS")

players = {}

for filename in os.listdir(NBA_DIR):

    if not filename.endswith(".json"):
        continue

    if filename == "games.json":
        continue

    path = os.path.join(
        NBA_DIR,
        filename
    )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            game = json.load(f)

        if isinstance(game, list):
            continue

        for p in game.get("players", []):

            name = p.get(
                "player",
                ""
            ).strip()

            if not name:
                continue

            if name not in players:

                players[name] = {
                    "player": name,
                    "team": p.get("team", ""),
                    "games": 0,
                    "points": 0,
                    "rebounds": 0,
                    "assists": 0,
                    "steals": 0,
                    "blocks": 0,
                    "turnovers": 0
                }

            players[name]["games"] += 1
            players[name]["points"] += int(
                p.get("points", 0)
            )
            players[name]["rebounds"] += int(
                p.get("rebounds", 0)
            )
            players[name]["assists"] += int(
                p.get("assists", 0)
            )
            players[name]["steals"] += int(
                p.get("steals", 0)
            )
            players[name]["blocks"] += int(
                p.get("blocks", 0)
            )
            players[name]["turnovers"] += int(
                p.get("turnovers", 0)
            )

    except Exception as e:

        print(f"FAILED PLAYER BUILD {filename}")
        print(str(e))

players_list = sorted(
    players.values(),
    key=lambda x: x["points"],
    reverse=True
)

with open(
    "docs/data/nba/players.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        players_list,
        f,
        indent=2
    )

print("PLAYERS.JSON UPDATED")

# BUILD PLAYER FILES

print("BUILDING PLAYER FILES")

player_games = {}

for filename in os.listdir(NBA_DIR):

    if not filename.endswith(".json"):
        continue

    if filename == "games.json":
        continue

    path = os.path.join(
        NBA_DIR,
        filename
    )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            game = json.load(f)

        if isinstance(game, list):
            continue

        game_id = game.get("game_id", "")
        date = game.get("date", "")

        home_team = game.get(
            "home_team",
            ""
        )

        away_team = game.get(
            "away_team",
            ""
        )

        for p in game.get("players", []):

            name = p.get(
                "player",
                ""
            ).strip()

            if not name:
                continue

            slug = (
                name.lower()
                .replace(".", "")
                .replace("'", "")
                .replace(" ", "-")
            )

            if slug not in player_games:

                player_games[slug] = {
                    "name": name,
                    "games": []
                }

            team = p.get("team", "")

            opp = (
                away_team
                if team == home_team
                else home_team
            )

            player_games[slug]["games"].append({

                "game_id": game_id,
                "date": date,
                "season": 2025,
                "team": team,
                "opp": opp,

                "pts": p.get("points", 0),
                "reb": p.get("rebounds", 0),
                "ast": p.get("assists", 0),
                "stl": p.get("steals", 0),
                "blk": p.get("blocks", 0),

                "game_type":
                    game.get(
                        "game_type",
                        "Playoffs"
                    )
            })

    except Exception as e:

        print(f"FAILED PLAYER FILE {filename}")
        print(str(e))

for slug, pdata in player_games.items():

    out_path = os.path.join(
        PLAYERS_DIR,
        f"{slug}.json"
    )

    with open(
        out_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pdata,
            f,
            indent=2
        )

print("PLAYER FILES UPDATED")
print("DONE")
