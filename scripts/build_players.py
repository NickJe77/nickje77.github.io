import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(parents=True, exist_ok=True)

players = {}

# ---------- CLEAN ----------
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
        return float(v)
    except:
        return 0

# 🔥 FIND PLAYERS ANYWHERE
def find_players(obj):
    found = []

    if isinstance(obj, dict):
        if "name" in obj or "player" in obj:
            found.append(obj)

        for v in obj.values():
            found.extend(find_players(v))

    elif isinstance(obj, list):
        for i in obj:
            found.extend(find_players(i))

    return found

print("🔥 Building NBA player files...")

game_count = 0

for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    print(f"→ {season_dir.name}")

    for game_file in season_dir.glob("*.json"):

        if game_file.name in ["index.json", "games.json"]:
            continue

        try:
            raw = json.loads(game_file.read_text())
        except:
            continue

        game = raw[0] if isinstance(raw, list) else raw
        if not isinstance(game, dict):
            continue

        game_id = game.get("game_id") or game.get("id") or ""
        date = game.get("date") or game.get("game_date") or ""
        season = game.get("season") or season_dir.name

        # 🔥 CRITICAL CHANGE — NO MORE home_players dependency
        plist = find_players(game)

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

            players[s]["games"].append({
                "game_id": game_id,
                "date": date,
                "season": season,
                "team": game.get("home_team") or "",
                "opponent": game.get("away_team") or "",

                "pts": num(p.get("pts") or p.get("points")),
                "reb": num(p.get("reb") or p.get("rebounds")),
                "ast": num(p.get("ast") or p.get("assists")),
                "stl": num(p.get("stl") or p.get("steals")),
                "blk": num(p.get("blk") or p.get("blocks"))
            })

            game_count += 1

# ---------- WRITE ----------
print("💾 Writing player files...")

written = 0

for s, data in players.items():
    if not data["games"]:
        continue

    (OUT / f"{s}.json").write_text(json.dumps(data, indent=2))
    written += 1

# ---------- INDEX ----------
index = [{"name": d["name"], "slug": s} for s, d in players.items() if d["games"]]
index.sort(key=lambda x: x["name"])

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("✅ DONE")
print(f"Players written: {written}")
print(f"Game entries: {game_count}")
