import json
from pathlib import Path
from datetime import datetime
import pytz

print("BUILDING ON THIS DAY (FINAL SAFE VERSION)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

today = datetime.now(pytz.timezone("Australia/Melbourne")).strftime("%m-%d")

data_out = {}

# -----------------------
# SAFE JSON LOAD
# -----------------------
def load_json_safe(path):
    try:
        text = path.read_text().strip()
        if not text:
            print(f"⚠️ Empty file skipped: {path}")
            return []
        return json.loads(text)
    except Exception as e:
        print(f"❌ Bad JSON skipped: {path} ({e})")
        return []

# -----------------------
# ENSURE VALID ROW
# -----------------------
def is_valid_row(r):
    return isinstance(r, dict)

# -----------------------
# GET DATE
# -----------------------
def get_date(row):
    return (
        row.get("date")
        or row.get("game_date")
        or row.get("match_date")
        or ""
    )

# -----------------------
# NORMALISE DATE
# -----------------------
def normalise(d):
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
def add_event(sport, row):
    if not is_valid_row(row):
        return

    d = normalise(get_date(row))
    if not d:
        return

    key = d.strftime("%m-%d")
    year = d.year

    team = row.get("team") or row.get("home_team")
    opp = row.get("opponent") or row.get("away_team")
    ts = row.get("team_score") or row.get("home_score")
    os = row.get("opponent_score") or row.get("away_score")

    if not team or not opp:
        return
    if ts is None or os is None:
        return

    text = f"{team} {ts} defeated {opp} {os}"

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])
    data_out[key][sport].append({
        "year": year,
        "text": text
    })

# -----------------------
# NBA (SKIP index.json)
# -----------------------
nba_dir = BASE / "nba" / "seasons"
if nba_dir.exists():
    for file in nba_dir.glob("*.json"):
        if file.name == "index.json":
            print(f"⏭️ Skipping index file: {file}")
            continue

        rows = load_json_safe(file)

        if not isinstance(rows, list):
            continue

        for r in rows:
            add_event("NBA", r)

# -----------------------
# AFL
# -----------------------
afl_dir = BASE / "afl"
if afl_dir.exists():
    for file in afl_dir.glob("afl_*.json"):
        rows = load_json_safe(file)

        if not isinstance(rows, list):
            continue

        for r in rows:
            add_event("AFL", r)

# -----------------------
# NRL
# -----------------------
nrl_dir = BASE / "nrl"
if nrl_dir.exists():
    for file in nrl_dir.rglob("*.json"):
        data = load_json_safe(file)

        rows = data if isinstance(data, list) else data.get("games", [])

        if not isinstance(rows, list):
            continue

        for r in rows:
            add_event("Football", r)

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

print(f"✅ Saved → {OUTPUT}")
