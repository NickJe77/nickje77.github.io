import json
from pathlib import Path
from datetime import datetime
import pytz

print("BUILDING ON THIS DAY (UNIVERSAL SCAN)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}

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
# NORMALISE DATE
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
# ADD EVENT
# -----------------------
def add_event(row, sport):

    if not isinstance(row, dict):
        return

    d = parse_date(row)
    if not d:
        return

    key = d.strftime("%m-%d")

    team = row.get("team") or row.get("home_team")
    opp = row.get("opponent") or row.get("away_team")

    ts = row.get("team_score") or row.get("home_score")
    os = row.get("opponent_score") or row.get("away_score")

    match_id = row.get("match_id") or row.get("game_id")

    if not team or not opp:
        return
    if ts is None or os is None:
        return

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
# DETECT SPORT FROM PATH
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
# WALK ALL FILES
# -----------------------
for file in BASE.rglob("*.json"):

    if file.name == "on_this_day.json":
        continue

    data = load_json_safe(file)
    if not data:
        continue

    sport = detect_sport(file)

    # CASE 1: dict with games
    if isinstance(data, dict):
        rows = data.get("games", [])
    # CASE 2: flat list
    elif isinstance(data, list):
        rows = data
    else:
        rows = []

    if not isinstance(rows, list):
        continue

    for row in rows:
        add_event(row, sport)

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
OUTPUT.write_text(json.dumps(data_out, indent=2))

print(f"✅ Built → {OUTPUT}")
