import json
import csv
import re
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY - FINAL FIX (AFL POST-2003 WORKING)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

# -----------------------
# DATE PARSER (AFL FIX)
# -----------------------
def parse_date(row):
    d = (
        row.get("date_iso")
        or row.get("date")
        or row.get("game_date")
        or row.get("match_date")
    )

    if not d:
        return None

    d = str(d)

    try:
        d = d.split(", ", 1)[1]
    except:
        pass

    d = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d)
    d = re.sub(r"\b[A-Z]{3,4}\b$", "", d).strip()

    for fmt in [
        "%d %B %Y, %I:%M %p",
        "%Y-%m-%d"
    ]:
        try:
            return datetime.strptime(d, fmt)
        except:
            pass

    return None

def add_event(d, sport, text):
    key = d.strftime("%m-%d")
    uid = f"{key}|{sport}|{d.year}|{text}"

    if uid in seen:
        return
    seen.add(uid)

    data_out.setdefault(key, {}).setdefault(sport, []).append({
        "year": d.year,
        "text": text
    })

# -----------------------
# AFL (REAL FIX)
# -----------------------
def process_afl_file(file):
    data = load_json_safe(file)
    if not isinstance(data, list):
        return

    matches = {}

    for row in data:
        if not isinstance(row, dict):
            continue

        d = parse_date(row)
        if not d:
            continue

        home = row.get("home_team") or row.get("played_for")
        away = row.get("away_team") or row.get("played_against")

        if not home or not away:
            continue

        # 🔥 CRITICAL FIX
        match_id = row.get("match_id")

        if not match_id:
            match_id = f"{d.strftime('%Y-%m-%d')}_{home}_{away}"

        if match_id not in matches:
            matches[match_id] = {
                "date": d,
                "home": home,
                "away": away,
                "hs": row.get("home_points"),
                "as": row.get("away_points"),
                "players": []
            }

        matches[match_id]["players"].append(row)

    for m in matches.values():
        try:
            hs = int(m["hs"])
            as_ = int(m["as"])
        except:
            continue

        if hs > as_:
            text = f"{m['home']} {hs} defeated {m['away']} {as_}"
        else:
            text = f"{m['away']} {as_} defeated {m['home']} {hs}"

        # stats
        best_disp = 0
        best_player = None

        for p in m["players"]:
            try:
                d_ = int(p.get("D") or 0)
                if d_ > best_disp:
                    best_disp = d_
                    best_player = p.get("player")
            except:
                pass

        if best_player and best_disp >= 30:
            text += f" — {best_player} {best_disp} disposals"

        add_event(m["date"], "AFL", text)

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*.json"):
    path = str(file).lower()

    if "afl" in path:
        process_afl_file(file)

# -----------------------
# SAVE
# -----------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(data_out, indent=2))

print("DONE")
