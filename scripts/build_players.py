import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(parents=True, exist_ok=True)

players = {}

# ---------- CLEAN NAME ----------
def clean_name(name):
    if not name:
        return ""
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return name.strip()

def slug(name):
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

print("🔥 Building NBA player files...")

game_count = 0
player_count = 0

# ---------- LOOP SEASONS ----------
for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    print(f"→ Processing season {season_dir.name}")

    for game_file in season_dir.glob("*.json"):

        if game_file.name in ["index.json", "games.json"]:
            continue

        try:
            game = json.loads(game_file.read_text())
        except:
            continue

        if not isinstance(game, dict):
            continue

        game_id = game.get("game_id") or game.get("id") or ""
        date = game.get("date") or game.get("game_date") or ""
        season = game.get("season") or season_dir.name

        teams = [
            ("home", game.get("home_team"), game.get("home_players", [])),
            ("away", game.get("away_team"), game.get("away_players", []))
        ]

        for side, team_name, plist in teams:

            for p in plist:

                name = clean_name(p.get("name") or p.get("player") or "")
                if not name:
                    continue

                s = slug(name)

                if s not in players:
                    players[s] = {
                        "name": name,
                        "games": []
                    }
                    player_count += 1

                players[s]["games"].append({
                    "game_id": game_id,
                    "date": date,
                    "season": season,
                    "team": team_name,
                    "opponent": game.get("away_team") if side == "home" else game.get("home_team"),

                    "pts": num(p.get("pts") or p.get("points")),
                    "reb": num(p.get("reb") or p.get("rebounds")),
                    "ast": num(p.get("ast") or p.get("assists")),
                    "stl": num(p.get("stl") or p.get("steals")),
                    "blk": num(p.get("blk") or p.get("blocks"))
                })

                game_count += 1

# ---------- WRITE FILES ----------
print("💾 Writing player files...")

for s, data in players.items():
    out_file = OUT / f"{s}.json"
    out_file.write_text(json.dumps(data, indent=2))

# ---------- BUILD INDEX ----------
index = []

for s, data in players.items():
    index.append({
        "name": data["name"],
        "slug": s
    })

index.sort(key=lambda x: x["name"])

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("✅ DONE")
print(f"Players: {player_count}")
print(f"Game entries: {game_count}")
