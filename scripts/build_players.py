import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(exist_ok=True)

players = {}

# ---------- NAME CLEAN ----------
def clean_name(name):
    name = str(name or "").strip()
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    name = re.sub(r"\s+", " ", name).strip()
    return name

def slug(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name

# Prefer full names over initials / shorter aliases
def better_display_name(current, candidate):
    current = clean_name(current)
    candidate = clean_name(candidate)

    if not current:
        return candidate
    if not candidate:
        return current

    # Prefer the longer, fuller-looking name
    cur_score = (
        len(current),
        current.count(" "),
        0 if re.search(r"\b[A-Z]\.", current) else 1
    )
    cand_score = (
        len(candidate),
        candidate.count(" "),
        0 if re.search(r"\b[A-Z]\.", candidate) else 1
    )
    return candidate if cand_score > cur_score else current

# ---------- SAFE NUMBER ----------
def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

# ---------- DATE PARSER ----------
def parse_date(d):
    try:
        return datetime.fromisoformat(str(d).replace("Z", ""))
    except:
        return datetime.min

# ---------- FILTER BAD GAMES ----------
def is_valid_game(game, team, opp):
    gt = str(game.get("game_type", "")).lower()

    if "all" in gt or "star" in gt:
        return False

    bad_names = {"world", "usa", "stars", "stripes"}
    if str(team).strip().lower() in bad_names:
        return False
    if str(opp).strip().lower() in bad_names:
        return False

    return True

print("Building NBA player database...")

# ---------- READ SEASONS ----------
season_dirs = sorted(
    [d for d in DATA.iterdir() if d.is_dir()],
    key=lambda x: x.name,
    reverse=True
)

for season_dir in season_dirs:
    season = season_dir.name

    game_files = [
        f for f in season_dir.iterdir()
        if f.is_file()
        and f.suffix == ".json"
        and f.name not in ["index.json", "games.json"]
    ]

    game_files.sort(key=lambda x: x.name, reverse=True)

    for game_file in game_files:
        try:
            game = json.loads(game_file.read_text())
        except:
            continue

        if not isinstance(game, dict):
            continue

        home = game.get("home_team")
        away = game.get("away_team")

        for p in game.get("players", []):
            raw_name = p.get("player_name") or p.get("name") or p.get("player")
            if not raw_name:
                continue

            display_name = clean_name(raw_name)
            key = slug(display_name)
            if not key:
                continue

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

            if not is_valid_game(game, team, opp):
                continue

            mins = p.get("min") or p.get("minutes") or p.get("mp") or 0

            if isinstance(mins, str) and ":" in mins:
                try:
                    m, s = mins.split(":")
                    mins = int(m) + int(s) / 60
                except:
                    mins = 0
            else:
                mins = num(mins)

            pts = num(p.get("points"))
            reb = num(p.get("rebounds"))
            ast = num(p.get("assists"))
            stl = num(p.get("steals"))
            blk = num(p.get("blocks"))

            # Skip only truly empty junk rows
            if mins == 0 and pts == 0 and reb == 0 and ast == 0 and stl == 0 and blk == 0:
                continue

            if key not in players:
                players[key] = {
                    "name": display_name,
                    "slug": key,
                    "aliases": [],
                    "teams": {},
                    "games": []
                }
            else:
                players[key]["name"] = better_display_name(players[key]["name"], display_name)

            if display_name and display_name not in players[key]["aliases"]:
                players[key]["aliases"].append(display_name)

            record = {
                "season": season,
                "game_id": game.get("game_id"),
                "date": game.get("date"),
                "team": team,
                "opponent": opp,
                "minutes": mins,
                "pts": pts,
                "reb": reb,
                "ast": ast,
                "stl": stl,
                "blk": blk
            }

            players[key]["games"].append(record)

            if team not in players[key]["teams"]:
                players[key]["teams"][team] = {
                    "games": 0,
                    "minutes": 0,
                    "pts": 0,
                    "reb": 0,
                    "ast": 0,
                    "stl": 0,
                    "blk": 0
                }

            t = players[key]["teams"][team]
            t["games"] += 1
            t["minutes"] += mins
            t["pts"] += pts
            t["reb"] += reb
            t["ast"] += ast
            t["stl"] += stl
            t["blk"] += blk

# ---------- DEDUPE GAME LOGS ----------
print("Deduping and sorting games...")

for player in players.values():
    seen = set()
    deduped = []

    for g in player["games"]:
        dedupe_key = (
            g.get("game_id"),
            g.get("date"),
            g.get("team"),
            g.get("opponent")
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(g)

    player["games"] = sorted(
        deduped,
        key=lambda x: parse_date(x.get("date", "")),
        reverse=True
    )

    player["aliases"] = sorted(set(player.get("aliases", [])))

# ---------- WRITE ----------
print("Writing player files...")

for f in OUT.glob("*.json"):
    f.unlink()

index = []

for key, data in players.items():
    path = OUT / f"{key}.json"

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    index.append({
        "name": data["name"],
        "slug": key
    })

# Dedupe index by slug
index_by_slug = {}
for item in index:
    s = item["slug"]
    if s not in index_by_slug:
        index_by_slug[s] = item
    else:
        index_by_slug[s]["name"] = better_display_name(index_by_slug[s]["name"], item["name"])

final_index = sorted(index_by_slug.values(), key=lambda x: x["name"])

with open(OUT / "index.json", "w") as f:
    json.dump(final_index, f, indent=2)

print("DONE")
print("Players:", len(final_index))
