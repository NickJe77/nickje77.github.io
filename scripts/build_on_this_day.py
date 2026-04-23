import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (FINAL WORKING VERSION)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# SAFE LOAD
# -----------------------
def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

# -----------------------
# DATE PARSER (ROWS)
# -----------------------
def parse_date(row):

    d = (
        row.get("date_iso")
        or row.get("date")
        or row.get("game_date")
        or row.get("match_date")
        or row.get("Date")
    )

    if not d:
        return None

    d = str(d).strip()

    try:
        return datetime.fromisoformat(d.replace("Z",""))
    except:
        pass

    try:
        return datetime.strptime(d[:10], "%Y-%m-%d")
    except:
        pass

    try:
        return datetime.strptime(d.replace(" ", "")[:10], "%d/%m/%Y")
    except:
        pass

    try:
        d = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', d)
        return datetime.strptime(d.strip(), "%d %B %Y")
    except:
        pass

    return None

# -----------------------
# SPORT DETECT
# -----------------------
def detect_sport(path):
    p = str(path).lower()
    if "nba" in p: return "NBA"
    if "afl" in p: return "AFL"
    if "nrl" in p: return "NRL"
    if "baseball" in p: return "MLB"
    if "tennis" in p: return "Tennis"
    if "golf" in p: return "Golf"
    if "cycling" in p: return "Cycling"
    if "bathurst" in p: return "Motorsport"
    if "f1" in p: return "F1"
    return None

# -----------------------
# FILTER FILES
# -----------------------
def is_valid_data_file(path):
    p = str(path).lower()
    if "players" in p: return False
    if "index.json" in p: return False
    if "on_this_day.json" in p: return False
    return True

# -----------------------
# ADD MATCH RESULT
# -----------------------
def add_event(row, sport, d):

    home = row.get("home_team") or row.get("played_for")
    away = row.get("away_team") or row.get("played_against")

    hs = row.get("home_score") or row.get("home_points")
    as_ = row.get("away_score") or row.get("away_points")

    if not home or not away:
        return

    try:
        hs = int(str(hs))
        as_ = int(str(as_))

        if hs > as_:
            text = f"{home} {hs} defeated {away} {as_}"
        elif as_ > hs:
            text = f"{away} {as_} defeated {home} {hs}"
        else:
            text = f"{home} {hs} drew with {away} {as_}"

    except:
        text = f"{home} vs {away}"

    key = d.strftime("%m-%d")

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])

    data_out[key][sport].append({
        "year": d.year,
        "text": text,
        "sport": sport
    })

# -----------------------
# AFL PLAYER STATS
# -----------------------
def add_afl_stats(row, d):

    player = row.get("player")
    goals = row.get("G")

    if not player or goals is None:
        return

    try:
        goals = int(goals)
    except:
        return

    if goals < 5:
        return

    key = d.strftime("%m-%d")

    uid = f"AFL|{d}|{player}|{goals}"
    if uid in seen:
        return
    seen.add(uid)

    data_out.setdefault(key, {})
    data_out[key].setdefault("AFL", [])

    data_out[key]["AFL"].append({
        "year": d.year,
        "text": f"{player} kicked {goals} goals",
        "sport": "AFL"
    })

# -----------------------
# NBA BOXSCORE PLAYER STATS
# -----------------------
def process_nba_boxscore(file):

    data = load_json_safe(file)
    if not data:
        return

    # ✅ DIRECT DATE FROM GAME OBJECT
    d_raw = data.get("date")
    if not d_raw:
        return

    try:
        d = datetime.fromisoformat(d_raw.replace("Z",""))
    except:
        return

    key = d.strftime("%m-%d")

    players = data.get("players", [])

    for p in players:

        name = p.get("player")
        pts = p.get("points")

        if not name or pts is None:
            continue

        try:
            pts = int(pts)
        except:
            continue

        if pts < 40:
            continue

        uid = f"NBA|{d}|{name}|{pts}"
        if uid in seen:
            continue
        seen.add(uid)

        data_out.setdefault(key, {})
        data_out[key].setdefault("NBA", [])

        data_out[key]["NBA"].append({
            "year": d.year,
            "text": f"{name} scored {pts} points",
            "sport": "NBA"
        })

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    if not file.is_file():
        continue

    # 🔥 NBA BOXSCORES
    if "nba" in str(file).lower() and "boxscores" in str(file).lower():
        process_nba_boxscore(file)
        continue

    if file.suffix.lower() != ".json":
        continue

    if not is_valid_data_file(file):
        continue

    sport = detect_sport(file)
    if not sport:
        continue

    data = load_json_safe(file)
    if not data:
        continue

    # AFL is flat list
    rows = data if isinstance(data, list) else data.get("games", [])

    for row in rows:

        if not isinstance(row, dict):
            continue

        d = parse_date(row)
        if not d:
            continue

        add_event(row, sport, d)

        if sport == "AFL":
            add_afl_stats(row, d)

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

print("✅ DONE")
print("Days built:", len(data_out))
