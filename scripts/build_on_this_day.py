import json
from pathlib import Path
from datetime import datetime
import pytz

print("BUILDING ON THIS DAY (UNIVERSAL + FLEXIBLE)")

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
# PARSE DATE (ALL FORMATS)
# -----------------------
def parse_date(row):
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
# ADD EVENT (FLEXIBLE)
# -----------------------
def add_event(row, sport):

    if not isinstance(row, dict):
        return

    d = parse_date(row)
    if not d:
        return

    key = d.strftime("%m-%d")

    # TEAM DETECTION
    team = (
        row.get("team")
        or row.get("home_team")
        or row.get("team_name")
    )

    opp = (
        row.get("opponent")
        or row.get("away_team")
        or row.get("opp")
        or row.get("opponent_team")
    )

    # SCORE DETECTION
    ts = (
        row.get("team_score")
        or row.get("home_score")
        or row.get("score")
    )

    os = (
        row.get("opponent_score")
        or row.get("away_score")
        or row.get("opp_score")
    )

    match_id = row.get("match_id") or row.get("game_id")

    # REQUIRE TEAMS
    if not team or not opp:
        return

    # BUILD TEXT
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
# WALK ALL FILES
# -----------------------
for file in BASE.rglob("*.json"):

    # skip output file
    if file.name == "on_this_day.json":
        continue

    data = load_json_safe(file)
    if not data:
        continue

    sport = detect_sport(file)

    # HANDLE STRUCTURES
    if isinstance(data, dict):
        rows = data.get("games", [])
    elif isinstance(data, list):
        rows = data
    else:
        rows = []

    if not isinstance(rows, list):
        continue

    for row in rows:
        add_event(row, sport)

# -----------------------
# SORT RESULTS
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
