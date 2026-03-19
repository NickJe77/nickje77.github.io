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
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

print("🔥 Building NBA player files (CORRECT TEAMS)...")

# ---------- LOOP ----------
for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    print(f"→ {season_dir.name}")

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

        home_team = game.get("home_team")
        away_team = game.get("away_team")

        # 🔥 THIS IS THE KEY FIX
        plist = game.get("players", [])

        for p in plist:

            name = clean_name(p.get("player") or p.get("name"))
            if not name:
                continue

            player_team = p.get("team")

            # 🚨 safety check
            if not player_team:
                continue

            # correct opponent
            opponent = away_team if player_team == home_team else home_team

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
                "team": player_team,
                "opponent": opponent,
                "pts": num(p.get("points")),
                "reb": num(p.get("rebounds")),
                "ast": num(p.get("assists")),
                "stl": num(p.get("steals")),
                "blk": num(p.get("blocks"))
            })

# ---------- WRITE ----------
print("💾 Writing players...")

for s, data in players.items():
    (OUT / f"{s}.json").write_text(json.dumps(data, indent=2))

index = sorted(
    [{"name": v["name"], "slug": k} for k,v in players.items()],
    key=lambda x: x["name"]
)

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("✅ DONE")
