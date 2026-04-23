import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (MERGED VERSION)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# LOAD
# -----------------------
def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

# -----------------------
# DATE
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
# SPORT
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
# FILTER
# -----------------------
def is_valid_data_file(path):
    p = str(path).lower()
    if "players" in p: return False
    if "index.json" in p: return False
    if "on_this_day.json" in p: return False
    return True

# -----------------------
# ADD FINAL EVENT
# -----------------------
def add_final_event(d, sport, text):

    key = d.strftime("%m-%d")

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])

    data_out[key][sport].append({
        "year": d.year,
        "text": text,
        "sport": sport
    })

# -----------------------
# AFL MATCH BUILDER (MERGED)
# -----------------------
def process_afl_file(file):

    data = load_json_safe(file)
    if not data:
        return

    matches = {}

    for row in data:

        d = parse_date(row)
        if not d:
            continue

        match_id = row.get("match_id")
        if not match_id:
            continue

        if match_id not in matches:
            matches[match_id] = {
                "date": d,
                "home": row.get("played_for"),
                "away": row.get("played_against"),
                "hs": row.get("home_points"),
                "as": row.get("away_points"),
                "players": []
            }

        matches[match_id]["players"].append(row)

    # BUILD OUTPUT
    for match_id, m in matches.items():

        uid = f"AFL|MATCH|{match_id}"
        if uid in seen:
            continue
        seen.add(uid)

        d = m["date"]
        home = m["home"]
        away = m["away"]

        try:
            hs = int(m["hs"])
            as_ = int(m["as"])

            if hs > as_:
                result = f"{home} {hs} defeated {away} {as_}"
            elif as_ > hs:
                result = f"{away} {as_} defeated {home} {hs}"
            else:
                result = f"{home} {hs} drew with {away} {as_}"
        except:
            result = f"{home} vs {away}"

        # 🔥 TOP GOAL KICKER
        top_player = None
        top_goals = 0

        for p in m["players"]:
            g = p.get("G")
            try:
                g = int(g)
            except:
                continue

            if g > top_goals:
                top_goals = g
                top_player = p.get("player")

        if top_player and top_goals >= 5:
            result += f" — {top_player} kicked {top_goals} goals"

        add_final_event(d, "AFL", result)

# -----------------------
# NBA MATCH BUILDER (MERGED)
# -----------------------
def process_nba_boxscore(file):

    data = load_json_safe(file)
    if not data:
        return

    d_raw = data.get("date")
    if not d_raw:
        return

    try:
        d = datetime.fromisoformat(d_raw.replace("Z",""))
    except:
        return

    game_id = data.get("game_id")

    uid = f"NBA|MATCH|{game_id}"
    if uid in seen:
        return
    seen.add(uid)

    home = data.get("home_team")
    away = data.get("away_team")
    hs = data.get("home_score")
    as_ = data.get("away_score")

    try:
        hs = int(hs)
        as_ = int(as_)

        if hs > as_:
            result = f"{home} {hs} defeated {away} {as_}"
        elif as_ > hs:
            result = f"{away} {as_} defeated {home} {hs}"
        else:
            result = f"{home} {hs} drew with {away} {as_}"
    except:
        result = f"{home} vs {away}"

    # 🔥 TOP SCORER
    players = data.get("players", [])

    top_player = None
    top_pts = 0

    for p in players:
        pts = p.get("points")
        try:
            pts = int(pts)
        except:
            continue

        if pts > top_pts:
            top_pts = pts
            top_player = p.get("player")

    if top_player and top_pts >= 40:
        result += f" — {top_player} scored {top_pts} points"

    add_final_event(d, "NBA", result)

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    if not file.is_file():
        continue

    path = str(file).lower()

    # NBA BOXSCORES
    if "nba" in path and "boxscores" in path:
        process_nba_boxscore(file)
        continue

    # AFL FILE
    if "afl" in path and file.suffix == ".json":
        process_afl_file(file)
        continue

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
