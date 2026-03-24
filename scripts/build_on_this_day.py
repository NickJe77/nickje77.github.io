import json
from pathlib import Path
from datetime import datetime
import pytz

print("BUILDING ON THIS DAY (CORRECT FORMAT)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

today = datetime.now(pytz.timezone("Australia/Melbourne")).strftime("%m-%d")

data_out = {}

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

    text = f"{team} {ts} defeated {opp} {os}"

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])
    data_out[key][sport].append({
        "year": year,
        "text": text
    })

# -----------------------
# NBA
# -----------------------
nba_dir = BASE / "nba" / "seasons"
if nba_dir.exists():
    for file in nba_dir.glob("*.json"):
        rows = json.loads(file.read_text())
        for r in rows:
            add_event("NBA", r)

# -----------------------
# AFL
# -----------------------
afl_dir = BASE / "afl"
if afl_dir.exists():
    for file in afl_dir.glob("afl_*.json"):
        rows = json.loads(file.read_text())
        for r in rows:
            add_event("AFL", r)

# -----------------------
# NRL (optional mapping to "Football")
# -----------------------
nrl_dir = BASE / "nrl"
if nrl_dir.exists():
    for file in nrl_dir.rglob("*.json"):
        data = json.loads(file.read_text())

        rows = data if isinstance(data, list) else data.get("games", [])

        for r in rows:
            add_event("Football", r)

# -----------------------
# SORT EACH SPORT BY YEAR DESC
# -----------------------
for day in data_out:
    for sport in data_out[day]:
        data_out[day][sport].sort(key=lambda x: x["year"], reverse=True)

# -----------------------
# SAVE
# -----------------------
OUTPUT.write_text(json.dumps(data_out, indent=2))

print(f"Saved → {OUTPUT}")
