import json
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY")

BASE = Path("docs/data")
OUTPUT = BASE / "onthisday.json"

today = datetime.utcnow().strftime("%m-%d")

results = []

# -----------------------
# SAFE GET DATE
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
def normalise_date(d):
    try:
        return datetime.fromisoformat(d).strftime("%m-%d")
    except:
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%m-%d")
        except:
            return None

# -----------------------
# ADD GAME
# -----------------------
def add_game(row, sport):
    results.append({
        "sport": sport,
        "season": row.get("season"),
        "date": get_date(row),
        "team": row.get("team") or row.get("home_team"),
        "opponent": row.get("opponent") or row.get("away_team"),
        "team_score": row.get("team_score") or row.get("home_score"),
        "opponent_score": row.get("opponent_score") or row.get("away_score"),
        "match_id": row.get("match_id") or row.get("game_id")
    })

# -----------------------
# NBA
# -----------------------
nba_dir = BASE / "nba" / "seasons"
if nba_dir.exists():
    for file in nba_dir.glob("*.json"):
        data = json.loads(file.read_text())
        for row in data:
            d = normalise_date(get_date(row))
            if d == today:
                add_game(row, "NBA")

# -----------------------
# AFL
# -----------------------
afl_dir = BASE / "afl"
if afl_dir.exists():
    for file in afl_dir.glob("afl_*.json"):
        data = json.loads(file.read_text())
        for row in data:
            d = normalise_date(get_date(row))
            if d == today:
                add_game(row, "AFL")

# -----------------------
# NRL
# -----------------------
nrl_dir = BASE / "nrl"
if nrl_dir.exists():
    for file in nrl_dir.rglob("*.json"):
        data = json.loads(file.read_text())

        if isinstance(data, list):
            rows = data
        else:
            rows = data.get("games", [])

        for row in rows:
            d = normalise_date(get_date(row))
            if d == today:
                add_game(row, "NRL")

# -----------------------
# SORT (newest first)
# -----------------------
results.sort(key=lambda x: x.get("date", ""), reverse=True)

# -----------------------
# SAVE
# -----------------------
OUTPUT.write_text(json.dumps(results, indent=2))

print(f"Saved {len(results)} games to {OUTPUT}")
