import os
import json
import requests
from datetime import datetime, timedelta

NBA_DIR = "docs/data/nba/2025"
PLAYERS_DIR = "docs/data/nba/players"

os.makedirs(NBA_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)

print("NBA PLAYOFF SAFE UPDATER")

headers = {
    "User-Agent": "Mozilla/5.0"
}

existing_ids = set()

for f in os.listdir(NBA_DIR):

    if f.endswith(".json"):

        existing_ids.add(
            f.replace(".json", "")
        )

print(f"EXISTING GAMES: {len(existing_ids)}")

# START AFTER YOUR LAST GAME
start = datetime(2026, 5, 4)

today = datetime.utcnow()

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

while start <= today:

    date_str = start.strftime("%Y-%m-%d")

    print(f"CHECKING {date_str}")

    try:

        scoreboard_url = (
            "https://cdn.nba.com/static/json/liveData/"
            f"scoreboard/todaysScoreboard_{date_str}.json"
        )

        r = requests.get(
            scoreboard_url,
            headers=headers,
            timeout=30
        )

        if r.status_code != 200:

            print(f"NO SCOREBOARD {date_str}")

            start += timedelta(days=1)
            continue

        data = r.json()

        games = (
            data.get("scoreboard", {})
            .get("games", [])
        )

        print(f"GAMES FOUND: {len(games)}")

        for g in games:

            game_id = str(
                g.get("gameId", "")
            )

            if not game_id:
                continue

            existing_path = os.path.join(
                NBA_DIR,
                f"{game_id}.json"
            )

            repair = False

            if game_id in existing_ids:

                try:

                    with open(
                        existing_path,
                        "r",
                        encoding="utf-8"
                    ) as ef:

                        existing_game = json.load(ef)

                    if isinstance(existing_game, list):

                        repair = True

                    elif not existing_game.get("players"):

                        repair = True

                    elif not existing_game.get("home_team"):

                        repair = True

                    elif not existing_game.get("away_team"):

                        repair = True

                    else:

                        print(f"SKIP GOOD {game_id}")
                        continue

                except:

                    repair = True

            if repair:

                print(f"REPAIRING {game_id}")

            else:

                print(f"NEW GAME {game_id}")

            box_url = (
                "https://cdn.nba.com/static/json/liveData/"
                f"boxscore/boxscore_{game_id}.json"
            )

            b = requests.get(
                box_url,
                headers=headers,
                timeout=30
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

# PLAYERS.JSON

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

# PLAYER FILES

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
                "blk": p.get("blocks", 0)
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
