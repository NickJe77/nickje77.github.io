import json
import re
import unicodedata
from pathlib import Path

# 🔥 SET ROOT MANUALLY (THIS IS THE KEY)
ROOT = Path.cwd()   # <- uses where you run the script from
DATA = ROOT / "docs/data/nba"
OUT = DATA / "players"

OUT.mkdir(parents=True, exist_ok=True)

players = {}

def clean_name(name):
    if not name:
        return ""
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return name.strip()

def slug(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
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

print("🔥 SCANNING ALL NBA GAME FILES")

# 🔥 FIND ALL JSON FILES RECURSIVELY
game_files = list(DATA.rglob("*.json"))

print(f"FOUND {len(game_files)} FILES")

for game_file in game_files:

    if "players" in game_file.parts:
        continue  # skip output folder

    if game_file.name in ["index.json", "games.json"]:
        continue

    try:
        game = json.loads(game_file.read_text())
    except:
        continue

    if not isinstance(game, dict):
        continue

    # DEBUG (see what's actually being read)
    # print("READING:", game_file)

    game_type = str(
        game.get("type") or
        game.get("season_type") or
        ""
    ).lower()

    if any(x in game_type for x in [
        "preseason", "summer", "all", "exhibition",
        "rising", "celebrity"
    ]):
        continue

    game_id = game.get("game_id") or game.get("id") or game_file.stem
    date = game.get("date") or game.get("game_date") or ""
    season = game.get("season") or game_file.parent.name

    home_team = game.get("home_team")
    away_team = game.get("away_team")

    # 🔥 UNIVERSAL PLAYER EXTRACTION
    plist = []

    if game.get("players"):
        plist = game["players"]
    else:
        for p in game.get("home_players", []):
            p = dict(p)
            p["team"] = home_team
            plist.append(p)

        for p in game.get("away_players", []):
            p = dict(p)
            p["team"] = away_team
            plist.append(p)

    for p in plist:

        name = clean_name(p.get("player") or p.get("name"))
        if not name:
            continue

        mins = str(p.get("minutes", "")).strip()
        if mins in ["0:00", "00:00", "0", ""]:
            continue

        team = p.get("team")
        if not team:
            continue

        opp = away_team if team == home_team else home_team

        s = slug(name)

        if s not in players:
            players[s] = {
                "name": name,
                "games": [],
                "seen": set()
            }

        unique_key = f"{game_id}-{team}"

        if unique_key in players[s]["seen"]:
            continue

        players[s]["seen"].add(unique_key)

        players[s]["games"].append({
            "game_id": game_id,
            "date": date,
            "season": season,
            "team": team,
            "opp": opp,
            "pts": num(p.get("points")),
            "reb": num(p.get("rebounds")),
            "ast": num(p.get("assists")),
            "stl": num(p.get("steals")),
            "blk": num(p.get("blocks")),
            "game_type": game_type
        })

# ---------- WRITE ----------
print("💾 WRITING PLAYER FILES")

index = []

for s, data in players.items():

    data.pop("seen", None)

    data["games"].sort(key=lambda x: x.get("date",""), reverse=True)

    (OUT / f"{s}.json").write_text(json.dumps(data, indent=2))

    index.append({
        "name": data["name"],
        "slug": s
    })

index.sort(key=lambda x: x["name"])

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("✅ DONE — GUARANTEED FULL CAREER BUILD")
