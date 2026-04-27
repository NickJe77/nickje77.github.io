import json
import csv
import re
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY - FINAL (NBA FIXED FOR YOUR STRUCTURE)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

def parse_date(row):
    if not isinstance(row, dict):
        return None

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
        return datetime.fromisoformat(d.replace("Z", "")[:19])
    except:
        pass

    for fmt in [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d %B %Y",
        "%B %d, %Y",
    ]:
        try:
            clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d)
            return datetime.strptime(clean[:30], fmt)
        except:
            pass

    return None

def add_event(d, sport, text):
    if not d or not sport or not text:
        return

    key = d.strftime("%m-%d")
    uid = f"{key}|{sport}|{d.year}|{text}"

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
# NBA (FIXED FOR YOUR DATA)
# -----------------------
def process_nba_boxscore(file):
    data = load_json_safe(file)
    if not isinstance(data, dict):
        return

    d = parse_date(data)
    if not d:
        return

    home = data.get("home_team")
    away = data.get("away_team")
    hs = data.get("home_score")
    as_ = data.get("away_score")

    scorers_30 = []

    for p in data.get("players", []):
        if not isinstance(p, dict):
            continue

        try:
            pts = int(p.get("points") or 0)
        except:
            continue

        if pts >= 30:
            name = (
                p.get("player_name")   # ✅ THIS WAS MISSING
                or p.get("player")
                or p.get("name")
                or p.get("full_name")
            )

            if name:
                scorers_30.append(f"{name} {pts}")

    if home and away and hs is not None and as_ is not None:
        try:
            hs = int(hs)
            as_ = int(as_)

            if hs > as_:
                text = f"{home} {hs} defeated {away} {as_}"
            elif as_ > hs:
                text = f"{away} {as_} defeated {home} {hs}"
            else:
                text = f"{home} {hs} drew with {away} {as_}"

            if scorers_30:
                text += " — " + ", ".join(scorers_30) + " pts"

            add_event(d, "NBA", text)

        except:
            pass

# -----------------------
# AFL (UNCHANGED WORKING)
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

    for m in matches.values():
        d = m["date"]

        try:
            hs = int(m["hs"])
            as_ = int(m["as"])

            if hs > as_:
                text = f"{m['home']} {hs} defeated {m['away']} {as_}"
            elif as_ > hs:
                text = f"{m['away']} {as_} defeated {m['home']} {hs}"
            else:
                text = f"{m['home']} {hs} drew with {m['away']} {as_}"
        except:
            continue

        top_goals = 0
        top_goals_player = None
        top_disp = 0
        top_disp_player = None

        for p in m["players"]:
            try:
                g = int(p.get("G") or 0)
                if g > top_goals:
                    top_goals = g
                    top_goals_player = p.get("player")
            except:
                pass

            try:
                d_ = int(p.get("D") or 0)
                if d_ > top_disp:
                    top_disp = d_
                    top_disp_player = p.get("player")
            except:
                pass

        extras = []

        if top_goals_player and top_goals >= 5:
            extras.append(f"{top_goals_player} {top_goals} goals")

        if top_disp_player and top_disp >= 30:
            extras.append(f"{top_disp_player} {top_disp} disposals")

        if extras:
            text += " — " + ", ".join(extras)

        add_event(d, "AFL", text)

# -----------------------
# MAIN LOOP (UNCHANGED)
# -----------------------
for file in BASE.rglob("*"):
    if not file.is_file():
        continue

    path = str(file).replace("\\", "/").lower()

    if path.endswith("on_this_day.json"):
        continue

    if file.suffix.lower() != ".json":
        continue

    if "/nba/" in path:
        process_nba_boxscore(file)
        continue

    if "/afl/" in path:
        process_afl_file(file)
        continue

# -----------------------
# SORT & SAVE
# -----------------------
for day in data_out:
    for sport in data_out[day]:
        data_out[day][sport].sort(
            key=lambda x: x.get("year", 0),
            reverse=True
        )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(data_out, indent=2), encoding="utf-8")

print("DONE")
