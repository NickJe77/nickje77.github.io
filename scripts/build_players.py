import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(exist_ok=True)

players = {}

def slug(name):
    s = unicodedata.normalize("NFD", name)
    s = s.encode("ascii", "ignore").decode("utf-8")
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s

def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

def is_valid_game(game):
    txt = json.dumps(game).lower()

    if "all-star" in txt:
        return False
    if "rising stars" in txt:
        return False
    if "celebrity" in txt:
        return False
    if "summer league" in txt:
        return False

    return True

def extract_players(game):
    # 🔥 HANDLE MULTIPLE STRUCTURES

    if "players" in game:
        return game["players"]

    if "player_stats" in game:
        return game["player_stats"]

    if "boxscore" in game:
        bs = game["boxscore"]
        if isinstance(bs, dict) and "players" in bs:
            return bs["players"]

    players = []

    if "home_players" in game:
        players.extend(game["home_players"])

    if "away_players" in game:
        players.extend(game["away_players"])

    return players


print("Building NBA player files...")

season_dirs = sorted(
    [d for d in DATA.iterdir() if d.is_dir()],
    key=lambda x: x.name,
    reverse=True
)

for season_dir in season_dirs:

    season = season_dir.name

    game_files = sorted(
        [f for f in season_dir.glob("*.json") if f.name not in ["index.json","games.json"]],
        key=lambda x: x.name,
        reverse=True
    )

    for game_file in game_files:

        try:
            game = json.loads(game_file.read_text())
        except:
            continue

        if not isinstance(game, dict):
            continue

        # 🔥 SKIP ALL-STAR ETC
        if not is_valid_game(game):
            continue

        home = game.get("home_team")
        away = game.get("away_team")

        players_list = extract_players(game)

        for p in players_list:

            name = p.get("player_name") or p.get("name") or p.get("player")

            if not name:
                continue

            key = slug(name)

            if key not in players:
                players[key] = {
                    "name": name,
                    "teams": {},
                    "games": []
                }

            team = p.get("team")
            if not team:
                continue

            opp = away if team == home else home

            record = {
                "season": season,
                "game_id": game.get("game_id"),
                "date": game.get("date"),
                "team": team,
                "opp": opp,
                "pts": num(p.get("points")),
                "reb": num(p.get("rebounds")),
                "ast": num(p.get("assists")),
                "stl": num(p.get("steals")),
                "blk": num(p.get("blocks"))
            }

            players[key]["games"].append(record)

            if team not in players[key]["teams"]:
                players[key]["teams"][team] = {
                    "games": 0,
                    "pts": 0,
                    "reb": 0,
                    "ast": 0,
                    "stl": 0,
                    "blk": 0
                }

            t = players[key]["teams"][team]

            t["games"] += 1
            t["pts"] += record["pts"]
            t["reb"] += record["reb"]
            t["ast"] += record["ast"]
            t["stl"] += record["stl"]
            t["blk"] += record["blk"]

print("Sorting game logs...")

for player in players.values():
    player["games"].sort(
        key=lambda g: g.get("date", ""),
        reverse=True
    )

print("Writing player files...")

index = []

for key, data in players.items():

    path = OUT / f"{key}.json"

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    index.append({
        "name": data["name"],
        "slug": key
    })

index.sort(key=lambda x: x["name"])

with open(OUT / "index.json", "w") as f:
    json.dump(index, f, indent=2)

print("NBA player database built successfully")
print("Players created:", len(index))
