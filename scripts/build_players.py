import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(exist_ok=True)

players = {}

# 🔥 NORMALISE NAME
def clean_name(name):
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return name.strip()

# 🔥 PLAYER ID
def player_id(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name

def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

def is_valid_game(game):
    gt = str(game.get("game_type", "")).lower()

    if "all" in gt and "star" in gt:
        return False
    if "preseason" in gt:
        return False
    if "summer" in gt:
        return False

    return True

def extract_players(game):
    players = []

    if isinstance(game.get("players"), list):
        players.extend(game["players"])

    if isinstance(game.get("player_stats"), list):
        players.extend(game["player_stats"])

    if isinstance(game.get("boxscore"), dict):
        if isinstance(game["boxscore"].get("players"), list):
            players.extend(game["boxscore"]["players"])

    if isinstance(game.get("home_players"), list):
        for p in game["home_players"]:
            p["team"] = game.get("home_team")
            players.append(p)

    if isinstance(game.get("away_players"), list):
        for p in game["away_players"]:
            p["team"] = game.get("away_team")
            players.append(p)

    if isinstance(game.get("home_team_players"), list):
        for p in game["home_team_players"]:
            p["team"] = game.get("home_team")
            players.append(p)

    if isinstance(game.get("away_team_players"), list):
        for p in game["away_team_players"]:
            p["team"] = game.get("away_team")
            players.append(p)

    return players


print("Building NBA player database...")

# 🔥 ENSURE SEASONS READ PROPERLY
season_dirs = sorted(
    [d for d in DATA.iterdir() if d.is_dir()],
    key=lambda x: x.name,
    reverse=True
)

for season_dir in season_dirs:

    season = season_dir.name

    # 🔥 CRITICAL FIX — DO NOT USE glob()
    game_files = list(season_dir.iterdir())

    game_files = [
        f for f in game_files
        if f.is_file()
        and f.suffix == ".json"
        and f.name not in ["index.json", "games.json"]
    ]

    # newest first
    game_files.sort(key=lambda x: x.name, reverse=True)

    for game_file in game_files:

        try:
            game = json.loads(game_file.read_text())
        except:
            continue

        if not isinstance(game, dict):
            continue

        if not is_valid_game(game):
            continue

        home = game.get("home_team")
        away = game.get("away_team")

        for p in extract_players(game):

            raw_name = p.get("player_name") or p.get("name") or p.get("player")

            if not raw_name:
                continue

            name = clean_name(raw_name)
            pid = player_id(name)

            if pid not in players:
                players[pid] = {
                    "player_id": pid,
                    "name": name,
                    "teams": {},
                    "games": []
                }

            team = p.get("team")

            if not team:
                continue

            # normalise team
            if team != home and team != away:
                if str(team).lower() in str(home).lower():
                    team = home
                elif str(team).lower() in str(away).lower():
                    team = away

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

            players[pid]["games"].append(record)

            if team not in players[pid]["teams"]:
                players[pid]["teams"][team] = {
                    "games": 0,
                    "pts": 0,
                    "reb": 0,
                    "ast": 0,
                    "stl": 0,
                    "blk": 0
                }

            t = players[pid]["teams"][team]

            t["games"] += 1
            t["pts"] += record["pts"]
            t["reb"] += record["reb"]
            t["ast"] += record["ast"]
            t["stl"] += record["stl"]
            t["blk"] += record["blk"]

print("Deduplicating + sorting...")

for player in players.values():

    seen = set()
    unique = []

    for g in player["games"]:
        key = (g["game_id"], g["team"])
        if key not in seen:
            seen.add(key)
            unique.append(g)

    player["games"] = sorted(
        unique,
        key=lambda x: x.get("date", ""),
        reverse=True
    )

print("Writing player files...")

# 🔥 CLEAN OLD FILES
for f in OUT.glob("*.json"):
    f.unlink()

index = []

for pid, data in players.items():

    path = OUT / f"{pid}.json"

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    index.append({
        "name": data["name"],
        "player_id": pid
    })

index.sort(key=lambda x: x["name"])

with open(OUT / "index.json", "w") as f:
    json.dump(index, f, indent=2)

print("DONE")
print("Players:", len(index))
