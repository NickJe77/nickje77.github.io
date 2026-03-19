import json
import re
import unicodedata
from pathlib import Path

# ---------- PATH ----------
ROOT = Path.cwd()
DATA = ROOT / "docs/data/nba"
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

print("🔥 BUILDING NBA PLAYER CAREERS")

# ---------- SCAN ALL FILES ----------
game_files = list(DATA.rglob("*.json"))

print(f"📂 Found {len(game_files)} JSON files")

for game_file in game_files:

    # skip output folder
    if "players" in game_file.parts:
        continue

    if game_file.name in ["index.json", "games.json"]:
        continue

    try:
        game = json.loads(game_file.read_text())
    except:
        continue

    if not isinstance(game, dict):
        continue

    # ---------- GAME TYPE FILTER ----------
    game_type = str(
        game.get("game_type") or
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

    # ---------- PLAYER EXTRACTION ----------
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

    # ---------- PROCESS ----------
    for p in plist:

        name = clean_name(
            p.get("player_name") or
            p.get("player") or
            p.get("name")
        )

        if not name:
            continue

        mins = str(p.get("minutes", "")).strip()
        if mins in ["0:00", "00:00", "0", ""]:
            continue

        team = (
            p.get("team") or
            p.get("team_name") or
            p.get("teamName")
        )

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
print("💾 Writing player files...")

index = []

for s, data in players.items():

    data.pop("seen", None)

    data["games"].sort(
        key=lambda x: x.get("date",""),
        reverse=True
    )

    (OUT / f"{s}.json").write_text(json.dumps(data, indent=2))

    index.append({
        "name": data["name"],
        "slug": s
    })

index.sort(key=lambda x: x["name"])

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("✅ DONE — FULL CAREER DATA BUILT")
