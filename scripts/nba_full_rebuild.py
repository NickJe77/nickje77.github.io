import os
import json
import requests
from datetime import datetime, timedelta

NBA_DIR = "docs/data/nba/2025"
PLAYERS_DIR = "docs/data/nba/players"

os.makedirs(NBA_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com"
})

print("NBA PLAYOFF SAFE UPDATER")

existing_ids = set()

for f in os.listdir(NBA_DIR):

    if f.endswith(".json"):

        existing_ids.add(
            f.replace(".json", "")
        )

print(f"EXISTING GAMES: {len(existing_ids)}")

today = datetime.utcnow()

# ONLY CHECK AFTER LAST GAME YOU HAVE
start = datetime(2026, 5, 4)

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

while start <= today:

    date_str = start.strftime("%Y-%m-%d")

    print(f"CHECKING {date_str}")

    try:

        schedule_url = (
            "https://stats.nba.com/stats/"
            f"scheduleleaguev2?"
            f"GameDate={date_str}"
            f"&LeagueID=00"
        )

        r = session.get(
            schedule_url,
            timeout=60
        )

        if r.status_code != 200:

            print(f"BAD SCHEDULE {date_str}")

            start += timedelta(days=1)
            continue

        data = r.json()

        result_sets = data.get("resultSets", [])

        if not result_sets:

            start += timedelta(days=1)
            continue

        result = result_sets[0]

        headers_row = result.get("headers", [])
        rows = result.get("rowSet", [])

        if "GAME_ID" not in headers_row:

            start += timedelta(days=1)
            continue

        game_id_index = headers_row.index("GAME_ID")

        for row in rows:

            try:

                game_id = str(
                    row[game_id_index]
                )

            except:

                continue

            if not game_id:
                continue

            existing_path = os.path.join(
                NBA_DIR,
                f"{game_id}.json"
            )

            if game_id in existing_ids:

                try:

                    with open(
                        existing_path,
                        "r",
                        encoding="utf-8"
                    ) as ef:

                        existing_game = json.load(ef)

                    if isinstance(existing_game, list):

                        print(f"REPAIR LIST {game_id}")

                    else:

                        existing_players = (
                            existing_game.get("players", [])
                        )

                        home_team = (
                            existing_game.get(
                                "home_team",
                                ""
                            )
                        )

                        away_team = (
                            existing_game.get(
                                "away_team",
                                ""
                            )
                        )

                        if (
                            existing_players
                            and home_team
                            and away_team
                        ):

                            print(f"SKIP GOOD {game_id}")
                            continue

                    print(f"REPAIRING {game_id}")

                except:

                    print(f"REBUILDING {game_id}")

            else:

                print(f"NEW GAME {game_id}")

            box_url = (
                "https://cdn.nba.com/static/json/liveData/"
                f"boxscore/boxscore_{game_id}.json"
            )

            b = session.get(
                box_url,
                timeout=60
            )

            if b.status_code != 200:

                print(f"BAD BOX {game_id}")
                continue

            raw = b.json()

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

                    stats = (
                        p.get("statistics", {})
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

            print(f"UPDATED {game_id}")

            existing_ids.add(game_id)

    except Exception as e:

        print(f"FAILED {date_str}")
        print(str(e))

    start += timedelta(days=1)

# BUILD PLAYERS.JSON

print("BUILDING PLAYERS")

players = {}

for filename in os.listdir(NBA_DIR):

    if not filename.endswith(".json"):
        continue

    if filename == "games.json":
        continue

    path = os.path.join(NBA_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

        if isinstance(game, list):
            continue

        for p in game.get("players", []):

            name = p.get("player", "").strip()

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
            players[name]["points"] += int(p.get("points", 0))
            players[name]["rebounds"] += int(p.get("rebounds", 0))
            players[name]["assists"] += int(p.get("assists", 0))
            players[name]["steals"] += int(p.get("steals", 0))
            players[name]["blocks"] += int(p.get("blocks", 0))
            players[name]["turnovers"] += int(p.get("turnovers", 0))

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

    json.dump(players_list, f, indent=2)

print("PLAYERS.JSON UPDATED")

# BUILD PLAYER FILES

print("BUILDING PLAYER FILES")

player_games = {}

for filename in os.listdir(NBA_DIR):

    if not filename.endswith(".json"):
        continue

    if filename == "games.json":
        continue

    path = os.path.join(NBA_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

        if isinstance(game, list):
            continue

        game_id = game.get("game_id", "")
        date = game.get("date", "")

        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")

        for p in game.get("players", []):

            name = p.get("player", "").strip()

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

                "game_type": "playoffs"
            })

    except Exception as e:

        print(f"FAILED PLAYER FILE {filename}")
        print(str(e))

for slug, pdata in player_games.items():

    out_path = os.path.join(
        PLAYERS_DIR,
        f"{slug}.json"
    )

    with open(out_path, "w", encoding="utf-8") as f:

        json.dump(pdata, f, indent=2)

print("PLAYER FILES UPDATED")
print("DONE")
