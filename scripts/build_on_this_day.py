import json
from pathlib import Path
from datetime import datetime
import pytz
import unicodedata
import re

print("BUILDING ON THIS DAY (PLAYERS + LINKS)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}

# -----------------------
# LOAD PLAYER MAP
# -----------------------
player_map = {}

players_dir = BASE / "nba" / "players"

if players_dir.exists():
    for file in players_dir.glob("*.json"):
        try:
            data = json.loads(file.read_text())

            name = data.get("name")
            pid = data.get("player_id")

            if name and pid:
                player_map[str(pid)] = name

        except:
            continue

print(f"Loaded {len(player_map)} NBA players")

# -----------------------
# SLUGIFY
# -----------------------
def slugify(name):
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\s-]", "", name)
    name = name.strip().lower()
    name = re.sub(r"\s+", "-", name)
    return name

# -----------------------
# SAFE LOAD
# -----------------------
def load_json_safe(path):
    try:
        text = path.read_text().strip()
        if not text:
            return None
        return json.loads(text)
    except:
        return None

# -----------------------
# PARSE DATE
# -----------------------
def parse_date(row):
    d = (
        row.get("date")
        or row.get("game_date")
        or row.get("match_date")
    )

    if not d:
        return None

    try:
        return datetime.fromisoformat(d)
    except:
        try:
            return datetime.strptime(d, "%Y-%m-%d")
        except:
            return None

# -----------------------
# DETECT SPORT
# -----------------------
def detect_sport(path):
    p = str(path).lower()

    if "nba" in p:
        return "NBA"
    if "afl" in p:
        return "AFL"
    if "nrl" in p:
        return "Football"

    return "Other"

# -----------------------
# ADD GAME
# -----------------------
def add_event(row, sport, d):

    key = d.strftime("%m-%d")

    team = row.get("team") or row.get("home_team")
    opp = row.get("opponent") or row.get("away_team")

    ts = row.get("team_score") or row.get("home_score")
    os = row.get("opponent_score") or row.get("away_score")

    match_id = row.get("match_id") or row.get("game_id")

    if not team or not opp:
        return

    if ts is None or os is None:
        text = f"{team} vs {opp}"
    else:
        text = f"{team} {ts} defeated {opp} {os}"

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])

    data_out[key][sport].append({
        "year": d.year,
        "text": text,
        "match_id": match_id,
        "sport": sport
    })

# -----------------------
# ADD PLAYER EVENTS
# -----------------------
def add_player_events(row, sport, d):

    players = row.get("players")
    if not players or not isinstance(players, list):
        return

    key = d.strftime("%m-%d")

    for p in players:

        # ---------- NBA ----------
        if sport == "NBA":

            pts = p.get("points", 0)
            reb = p.get("rebounds", 0)
            ast = p.get("assists", 0)

            pid = str(p.get("player_id"))
            name = player_map.get(pid, f"Player {pid}")

            # SLUG FOR LINK
            slug = slugify(name)

            if pts >= 50:
                text = f"<a href='nba-player.html?player={slug}'>{name}</a> scored {pts} points"

            elif sum(x >= 10 for x in [pts, reb, ast]) >= 3:
                text = f"<a href='nba-player.html?player={slug}'>{name}</a> recorded a triple-double"

            else:
                continue

            data_out.setdefault(key, {})
            data_out[key].setdefault("NBA", []).append({
                "year": d.year,
                "text": text,
                "sport": "NBA"
            })

        # ---------- AFL ----------
        if sport == "AFL":

            goals = p.get("goals", 0)
            name = p.get("player_name") or "Unknown"

            slug = slugify(name)

            if goals >= 8:
                text = f"<a href='afl-player.html?player={slug}'>{name}</a> kicked {goals} goals"
            else:
                continue

            data_out.setdefault(key, {})
            data_out[key].setdefault("AFL", []).append({
                "year": d.year,
                "text": text,
                "sport": "AFL"
            })

        # ---------- NRL ----------
        if sport == "Football":

            tries = p.get("tries", 0)
            name = p.get("player_name") or "Unknown"

            slug = slugify(name)

            if tries >= 3:
                text = f"<a href='nrl-player.html?player={slug}'>{name}</a> scored {tries} tries"
            else:
                continue

            data_out.setdefault(key, {})
            data_out[key].setdefault("Football", []).append({
                "year": d.year,
                "text": text,
                "sport": "Football"
            })

# -----------------------
# WALK FILES
# -----------------------
for file in BASE.rglob("*.json"):

    if file.name == "on_this_day.json":
        continue

    data = load_json_safe(file)
    if not data:
        continue

    sport = detect_sport(file)

    if isinstance(data, dict):
        rows = data.get("games", [])
    elif isinstance(data, list):
        rows = data
    else:
        continue

    for row in rows:

        d = parse_date(row)
        if not d:
            continue

        add_event(row, sport, d)
        add_player_events(row, sport, d)

# -----------------------
# SORT
# -----------------------
for day in data_out:
    for sport in data_out[day]:
        data_out[day][sport].sort(key=lambda x: x["year"], reverse=True)

# -----------------------
# SAVE
# -----------------------
OUTPUT.write_text(json.dumps(data_out, indent=2))

print("✅ DONE")
