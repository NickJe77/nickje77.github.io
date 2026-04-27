import json
import csv
import re
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY - FINAL (ALL SPORTS + AFL FIX)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# SAFE LOAD
# -----------------------
def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

# -----------------------
# DATE PARSER (AFL FIX INCLUDED)
# -----------------------
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

    # AFL style cleanup
    try:
        d = d.split(", ", 1)[1]
    except:
        pass

    d = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d)
    d = re.sub(r"\b[A-Z]{3,4}\b$", "", d).strip()

    for fmt in [
        "%d %B %Y, %I:%M %p",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]:
        try:
            return datetime.strptime(d, fmt)
        except:
            continue

    return None

# -----------------------
# ADD EVENT
# -----------------------
def add_event(d, sport, text):
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
# NBA
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

    try:
        hs = int(data.get("home_score"))
        as_ = int(data.get("away_score"))
    except:
        return

    scorers_30 = []

    for p in data.get("players", []):
        try:
            pts = int(p.get("points") or 0)
        except:
            continue

        if pts >= 30:
            name = p.get("player_name") or p.get("player") or p.get("name")
            if name:
                scorers_30.append(f"{name} {pts}")

    if hs > as_:
        text = f"{home} {hs} defeated {away} {as_}"
    else:
        text = f"{away} {as_} defeated {home} {hs}"

    if scorers_30:
        text += " — " + ", ".join(scorers_30) + " pts"

    add_event(d, "NBA", text)

# -----------------------
# AFL (FIXED PROPERLY)
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

        # 🔥 FIX: don't rely only on match_id
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
# MLB
# -----------------------
def process_mlb_boxscore(file):
    data = load_json_safe(file)
    if not isinstance(data, dict):
        return

    d = parse_date(data)
    if not d:
        return

    try:
        hs = int(data.get("home_score"))
        as_ = int(data.get("away_score"))
    except:
        return

    home = data.get("home_team")
    away = data.get("away_team")

    if hs > as_:
        text = f"{home} {hs} defeated {away} {as_}"
    else:
        text = f"{away} {as_} defeated {home} {hs}"

    add_event(d, "MLB", text)

# -----------------------
# GENERIC (NRL etc)
# -----------------------
def process_generic_file(file, sport):
    data = load_json_safe(file)
    if not data:
        return

    rows = data if isinstance(data, list) else data.get("games", [])

    for row in rows:
        d = parse_date(row)
        if not d:
            continue

        home = row.get("home_team") or row.get("home")
        away = row.get("away_team") or row.get("away")

        try:
            hs = int(row.get("home_score") or row.get("home_points"))
            as_ = int(row.get("away_score") or row.get("away_points"))
        except:
            continue

        if hs > as_:
            text = f"{home} {hs} defeated {away} {as_}"
        else:
            text = f"{away} {as_} defeated {home} {hs}"

        add_event(d, sport, text)

# -----------------------
# RACING
# -----------------------
def process_racing_csv(file):
    try:
        with open(file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                d = parse_date({"date": r.get("Date")})
                if not d:
                    continue
                race = r.get("Race")
                winner = r.get("Winner")
                if race and winner:
                    add_event(d, "Racing", f"{winner} won the {race}")
    except:
        pass

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):
    if not file.is_file():
        continue

    path = str(file).lower()

    if file.suffix == ".csv":
        process_racing_csv(file)
        continue

    if file.suffix != ".json":
        continue

    if "nba" in path:
        process_nba_boxscore(file)
        continue

    if "afl" in path:
        process_afl_file(file)
        continue

    if "baseball" in path:
        process_mlb_boxscore(file)
        continue

    if "nrl" in path:
        process_generic_file(file, "NRL")
        continue

# -----------------------
# SAVE
# -----------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(data_out, indent=2), encoding="utf-8")

print("DONE")
