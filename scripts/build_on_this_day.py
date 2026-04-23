import json
from pathlib import Path
from datetime import datetime
import unicodedata
import re

print("BUILDING ON THIS DAY (LOCKED + MULTI-SPORT)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

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
        print(f"❌ Skipped bad JSON: {path}")
        return None

# -----------------------
# PARSE DATE
# -----------------------
def parse_date(row):
    if not isinstance(row, dict):
        return None

    d = (
        row.get("date")
        or row.get("game_date")
        or row.get("match_date")
        or row.get("Date")
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
    if "baseball" in p:
        return "MLB"

    return None

# -----------------------
# LOAD NBA PLAYERS
# -----------------------
player_map = {}
players_dir = BASE / "nba" / "players"

if players_dir.exists():
    for file in players_dir.glob("*.json"):
        data = load_json_safe(file)
        if not data:
            continue

        name = file.stem.replace("-", " ").title()
        pid = data.get("player_id") if isinstance(data, dict) else None

        if pid:
            player_map[str(pid)] = name

print(f"Loaded {len(player_map)} NBA players")

# -----------------------
# VALID GAME CHECK
# -----------------------
def is_game_row(row):
    return isinstance(row, dict) and (
        "home_team" in row
        or "team" in row
        or "away_team" in row
    )

# -----------------------
# ADD GAME EVENT
# -----------------------
def add_event(row, sport, d):

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

    key = d.strftime("%m-%d")

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
    if not isinstance(players, list):
        return

    key = d.strftime("%m-%d")

    for p in players:

        if not isinstance(p, dict):
            continue

        # NBA
        if sport == "NBA":
            pts = p.get("points", 0)
            reb = p.get("rebounds", 0)
            ast = p.get("assists", 0)

            pid = str(p.get("player_id"))
            name = player_map.get(pid, f"Player {pid}")
            slug = slugify(name)

            if pts >= 50:
                text = f"<a href='nba-player.html?player={slug}'>{name}</a> scored {pts} points"
            elif sum(x >= 10 for x in [pts, reb, ast]) >= 3:
                text = f"<a href='nba-player.html?player={slug}'>{name}</a> recorded a triple-double"
            else:
                continue

        # AFL
        elif sport == "AFL":
            goals = p.get("goals", 0)
            name = p.get("player_name") or "Unknown"
            slug = slugify(name)

            if goals >= 8:
                text = f"<a href='afl-player.html?player={slug}'>{name}</a> kicked {goals} goals"
            else:
                continue

        # NRL
        elif sport == "Football":
            tries = p.get("tries", 0)
            name = p.get("player_name") or "Unknown"
            slug = slugify(name)

            if tries >= 3:
                text = f"<a href='nrl-player.html?player={slug}'>{name}</a> scored {tries} tries"
            else:
                continue

        else:
            continue

        data_out.setdefault(key, {})
        data_out[key].setdefault(sport, [])

        data_out[key][sport].append({
            "year": d.year,
            "text": text,
            "sport": sport
        })

# -----------------------
# TARGET DIRECTORIES ONLY
# -----------------------
TARGET_DIRS = [
    BASE / "nba" / "seasons",
    BASE / "afl",
    BASE / "nrl",
    BASE / "baseball" / "seasons"
]

# -----------------------
# MAIN LOOP (DEDUPED)
# -----------------------
for dir_path in TARGET_DIRS:

    if not dir_path.exists():
        continue

    for file in dir_path.rglob("*.json"):

        if file.name == "on_this_day.json":
            continue

        sport = detect_sport(file)
        if not sport:
            continue

        data = load_json_safe(file)
        if not data:
            continue

        if isinstance(data, dict):
            rows = data.get("games")
            if not isinstance(rows, list):
                continue
        elif isinstance(data, list):
            rows = data
        else:
            continue

        for row in rows:

            if not is_game_row(row):
                continue

            d = parse_date(row)
            if not d:
                continue

            uid = f"{sport}_{row.get('game_id')}_{d}"

            if uid in seen:
                continue
            seen.add(uid)

            add_event(row, sport, d)
            add_player_events(row, sport, d)

# -----------------------
# SORT
# -----------------------
for day in data_out:
    for sport in data_out[day]:
        data_out[day][sport].sort(
            key=lambda x: x["year"],
            reverse=True
        )

# -----------------------
# SAVE
# -----------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(data_out, indent=2))

print(f"✅ DONE → {OUTPUT}")
