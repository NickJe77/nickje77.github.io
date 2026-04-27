import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (FINAL – CORRECT FILE)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"   # ✅ CORRECT FILE NAME

data_out = {}
seen = set()

# -----------------------
# LOAD JSON SAFE
# -----------------------
def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

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
# ADD EVENT
# -----------------------
def add_event(d, sport, text):
    key = d.strftime("%m-%d")

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])

    data_out[key][sport].append({
        "year": d.year,
        "text": text,
        "sport": sport
    })

# -----------------------
# NBA (FIXED)
# -----------------------
def process_nba(file):
    data = load_json_safe(file)
    if not data or "game_id" not in data:
        return

    d = parse_date(data)
    if not d:
        return

    uid = f"NBA|{data.get('game_id')}"
    if uid in seen:
        return
    seen.add(uid)

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

    top_player = None
    top_pts = 0

    for p in data.get("players", []):
        try:
            pts = (
                p.get("points")
                or p.get("PTS")
                or p.get("pts")
                or 0
            )
            pts = int(pts)

            if pts > top_pts:
                top_pts = pts
                top_player = p.get("player") or p.get("name")
        except:
            continue

    if top_player and top_pts >= 40:
        result += f" — {top_player} scored {top_pts} points"

    add_event(d, "NBA", result)

# -----------------------
# AFL
# -----------------------
def process_afl(file):
    data = load_json_safe(file)
    if not data:
        return

    matches = {}

    for row in data:
        d = parse_date(row)
        if not d:
            continue

        mid = row.get("match_id")
        if not mid:
            continue

        matches.setdefault(mid, {
            "date": d,
            "home": row.get("played_for"),
            "away": row.get("played_against"),
            "hs": row.get("home_points"),
            "as": row.get("away_points")
        })

    for mid, m in matches.items():

        uid = f"AFL|{mid}"
        if uid in seen:
            continue
        seen.add(uid)

        d = m["date"]

        try:
            hs = int(m["hs"])
            as_ = int(m["as"])

            if hs > as_:
                text = f"{m['home']} {hs} defeated {m['away']} {as_}"
            else:
                text = f"{m['away']} {as_} defeated {m['home']} {hs}"
        except:
            text = f"{m['home']} vs {m['away']}"

        add_event(d, "AFL", text)

# -----------------------
# RACING CSV (UTF FIX)
# -----------------------
def process_racing(file):

    try:
        with open(file, newline='', encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for r in reader:

                dt = parse_date({"date": r.get("Date") or r.get("date")})
                if not dt:
                    continue

                race = r.get("Race") or r.get("race")
                winner = r.get("Winner") or r.get("winner")

                if not race or not winner:
                    continue

                uid = f"RACING|{dt}|{race}|{winner}"
                if uid in seen:
                    continue
                seen.add(uid)

                add_event(dt, "Racing", f"{winner.strip()} won the {race.strip()}")

    except Exception as e:
        print("CSV error:", file, e)

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    if not file.is_file():
        continue

    path = str(file).lower()

    if file.suffix.lower() == ".csv":
        process_racing(file)
        continue

    if "nba" in path and "boxscores" in path:
        process_nba(file)
        continue

    if "afl" in path:
        process_afl(file)
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
# SAVE (FORCED)
# -----------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

if not data_out:
    print("⚠️ No data built — writing empty file")
    OUTPUT.write_text("{}")
else:
    OUTPUT.write_text(json.dumps(data_out, indent=2))

print("DONE")
print("Days built:", len(data_out))
print("Saved to:", OUTPUT)
