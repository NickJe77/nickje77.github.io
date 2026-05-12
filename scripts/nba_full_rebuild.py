import os
import json
import requests
from datetime import datetime, timedelta

NBA_DIR = "docs/data/nba/2025"

os.makedirs(NBA_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/"
}

print("NBA SAFE UPDATER")

existing_ids = set()

for f in os.listdir(NBA_DIR):

    if f.endswith(".json"):

        existing_ids.add(
            f.replace(".json", "")
        )

print(f"EXISTING GAMES: {len(existing_ids)}")

today = datetime.utcnow()

start = datetime(2025, 10, 1)

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
            "https://cdn.nba.com/static/json/liveData/"
            f"scoreboard/todaysScoreboard_{date_str}.json"
        )

        r = requests.get(
            schedule_url,
            headers=headers,
            timeout=30
        )

        if r.status_code != 200:
            start += timedelta(days=1)
            continue

        data = r.json()

        games = (
            data.get("scoreboard", {})
            .get("games", [])
        )

        for g in games:

            game_id = g.get("gameId")

            if not game_id:
                continue

            if game_id in existing_ids:

                print(f"SKIP {game_id}")
                continue

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
                    game.get("arena", {}).get("arenaName", ""),

                "attendance":
                    safe_int(game.get("attendance")),

                "players": []
            }

            for side, team_name in [
                (home, home_team),
                (away, away_team)
            ]:

                for p in side.get("players", []):

                    if p.get("played") != "1":
                        continue

                    stats = p.get("statistics", {})

                    full_name = (
                        f"{p.get('firstName', '')} "
                        f"{p.get('familyName', '')}"
                    ).strip()

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

            out_path = os.path.join(
                NBA_DIR,
                f"{game_id}.json"
            )

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

            print(f"ADDED {game_id}")

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

    path = os.path.join(NBA_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

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

    json.dump(players_list, f, indent=2)

print("PLAYERS UPDATED")
print("DONE")
