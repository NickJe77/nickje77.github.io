import json
from pathlib import Path
from datetime import datetime
import unicodedata
import re

print("BUILDING ON THIS DAY (ALL SPORTS AUTO)")

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
        text = path.read_text(encoding="utf-8").strip()
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
    d = (
        row.get("date")
        or row.get("game_date")
        or row.get("match_date")
        or row.get("Date")
        or row.get("gameDate")
    )

    if not d:
        return None

    try:
        return datetime.fromisoformat(str(d).replace("Z",""))
    except:
        try:
            return datetime.strptime(str(d)[:10], "%Y-%m-%d")
        except:
            return None

# -----------------------
# DETECT SPORT (AUTO)
# -----------------------
def detect_sport(path):
    p = str(path).lower()

    if "nba" in p:
        return "NBA"
    if "afl" in p:
        return "AFL"
    if "nrl" in p:
        return "NRL"
    if "baseball" in p:
        return "MLB"
    if "tennis" in p:
        return "Tennis"
    if "golf" in p:
        return "Golf"
    if "cycling" in p:
        return "Cycling"
    if "bathurst" in p:
        return "Motorsport"
    if "f1" in p:
        return "F1"

    return None

# -----------------------
# FILTER FILES (CRITICAL)
# -----------------------
def is_valid_data_file(path):
    p = str(path).lower()

    # ❌ skip junk
    if "players" in p:
        return False
    if "boxscores" in p:
        return False
    if "index.json" in p:
        return False
    if "on_this_day.json" in p:
        return False

    return True

# -----------------------
# EXTRACT ROWS (ALL FORMATS)
# -----------------------
def extract_rows(data):

    # list format
    if isinstance(data, list):
        return data

    # dict formats
    if isinstance(data, dict):

        if "games" in data:
            return data["games"]

        if "matches" in data:
            return data["matches"]

        if "dates" in data:
            rows = []
            for d in data["dates"]:
                rows.extend(d.get("games", []))
            return rows

    return []

# -----------------------
# ADD EVENT
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
# MAIN LOOP (AUTO)
# -----------------------
for file in BASE.rglob("*.json"):

    if not is_valid_data_file(file):
        continue

    sport = detect_sport(file)
    if not sport:
        continue

    data = load_json_safe(file)
    if not data:
        continue

    rows = extract_rows(data)

    for row in rows:

        if not isinstance(row, dict):
            continue

        d = parse_date(row)
        if not d:
            continue

        uid = f"{sport}|{d}|{row.get('game_id')}|{row.get('match_id')}"

        if uid in seen:
            continue
        seen.add(uid)

        add_event(row, sport, d)

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
