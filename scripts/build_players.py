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

# ---------- STRONG SLUG (NO DUPES) ----------
def slug(name):
    name = clean_name(name).lower()

    # remove punctuation
    name = re.sub(r"[^\w\s-]", "", name)

    # collapse spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name.replace(" ", "-")

def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

print("🔥 Building NBA players (NO DUPES + NO 0 MINUTES)...")

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

        plist = game.get("players", [])

        for p in plist:

            name = clean_name(p.get("player") or p.get("name"))
            if not name:
                continue

            # 🔥 REMOVE 0 MINUTE GAMES
            mins = str(p.get("minutes", "")).strip()
            if mins in ["0:00", "00:00", "0", ""]:
                continue

            player_team = p.get("team")
            if not player_team:
                continue

            opponent = away_team if player_team == home_team else home_team

            s = slug(name)

            if s not in players:
                players[s] = {
                    "name": name,
                    "games": [],
                    "seen": set()  # 🔥 prevents duplicate games
                }

            # 🔥 DUPLICATE GAME PROTECTION
            unique_key = f"{game_id}-{player_team}"

            if unique_key in players[s]["seen"]:
                continue

            players[s]["seen"].add(unique_key)

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

index = []

for s, data in players.items():

    # remove helper set before saving
    data.pop("seen", None)

    # sort games newest first
    data["games"].sort(key=lambda x: (x.get("date","")), reverse=True)

    (OUT / f"{s}.json").write_text(json.dumps(data, indent=2))

    index.append({
        "name": data["name"],
        "slug": s
    })

index.sort(key=lambda x: x["name"])

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("✅ DONE")
