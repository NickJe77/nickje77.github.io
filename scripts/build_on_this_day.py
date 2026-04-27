import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (MERGE MODE)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# LOAD EXISTING FILE
# -----------------------
if OUTPUT.exists():
    try:
        data_out = json.loads(OUTPUT.read_text(encoding="utf-8"))
        print("Loaded existing file")
    except:
        data_out = {}

# build seen set from existing
for day in data_out:
    for sport in data_out[day]:
        for e in data_out[day][sport]:
            key = f"{sport}|{e['year']}|{e['text']}"
            seen.add(key)

# -----------------------
# DATE PARSER
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

    for fmt in ["%Y-%m-%d", "%d/%m/%Y"]:
        try:
            return datetime.strptime(d[:10], fmt)
        except:
            pass

    try:
        d = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', d)
        return datetime.strptime(d.strip(), "%d %B %Y")
    except:
        pass

    return None

# -----------------------
# ADD EVENT (NO DUPES)
# -----------------------
def add_event(d, sport, text):
    key = d.strftime("%m-%d")
    uid = f"{sport}|{d.year}|{text}"

    if uid in seen:
        return

    seen.add(uid)

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])

    data_out[key][sport].append({
        "year": d.year,
        "text": text,
        "sport": sport
    })

# -----------------------
# GENERIC (NRL / MLB / ETC)
# -----------------------
def process_generic(file, sport):

    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except:
        return

    rows = data if isinstance(data, list) else data.get("games", [])

    for row in rows:
        if not isinstance(row, dict):
            continue

        d = parse_date(row)
        if not d:
            continue

        home = row.get("home_team") or row.get("team")
        away = row.get("away_team") or row.get("opponent")

        hs = row.get("home_score") or row.get("team_score")
        as_ = row.get("away_score") or row.get("opponent_score")

        if not home or not away:
            continue

        try:
            hs = int(hs)
            as_ = int(as_)

            if hs > as_:
                text = f"{home} {hs} defeated {away} {as_}"
            elif as_ > hs:
                text = f"{away} {as_} defeated {home} {hs}"
            else:
                text = f"{home} {hs} drew with {away} {as_}"
        except:
            text = f"{home} vs {away}"

        add_event(d, sport, text)

# -----------------------
# NBA
# -----------------------
def process_nba(file):
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except:
        return

    if "game_id" not in data:
        return

    d = parse_date(data)
    if not d:
        return

    home = data.get("home_team")
    away = data.get("away_team")

    try:
        hs = int(data.get("home_score"))
        as_ = int(data.get("away_score"))

        if hs > as_:
            result = f"{home} {hs} defeated {away} {as_}"
        else:
            result = f"{away} {as_} defeated {home} {hs}"
    except:
        result = f"{home} vs {away}"

    # high scorer
    top_player = None
    top_pts = 0

    for p in data.get("players", []):
        try:
            pts = int(p.get("PTS") or p.get("points") or 0)
            if pts > top_pts:
                top_pts = pts
                top_player = p.get("player")
        except:
            pass

    if top_player and top_pts >= 40:
        result += f" — {top_player} scored {top_pts}"

    add_event(d, "NBA", result)

# -----------------------
# RACING CSV
# -----------------------
def process_racing(file):

    try:
        with open(file, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for r in reader:

                dt = parse_date({"date": r.get("Date")})
                if not dt:
                    continue

                race = r.get("Race")
                winner = r.get("Winner")

                if not race or not winner:
                    continue

                add_event(dt, "Racing", f"{winner} won the {race}")

    except:
        pass

# -----------------------
# DETECT SPORT
# -----------------------
def detect_sport(path):
    p = str(path).lower()
    if "nrl" in p: return "NRL"
    if "baseball" in p: return "MLB"
    if "tennis" in p: return "Tennis"
    if "golf" in p: return "Golf"
    if "cycling" in p: return "Cycling"
    return None

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    path = str(file).lower()

    if not file.is_file():
        continue

    if file.suffix == ".csv":
        process_racing(file)
        continue

    if "nba" in path and "boxscores" in path:
        process_nba(file)
        continue

    if path.endswith(".json"):
        sport = detect_sport(file)
        if sport:
            process_generic(file, sport)

# -----------------------
# SAVE
# -----------------------
OUTPUT.write_text(json.dumps(data_out, indent=2))

print("DONE")
print("Days:", len(data_out))
