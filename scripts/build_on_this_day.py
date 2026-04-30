import json
import csv
import re
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY - FINAL (AFL HIGH STATS FIX)")

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
# DATE PARSER
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

    d = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d)
    d = re.sub(r"\b[A-Z]{3,4}\b$", "", d).strip()

    for fmt in [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d %B %Y",
        "%B %d %Y",
        "%d %b %Y",
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
        "text": text
    })

# -----------------------
# HORSE RACING
# -----------------------
def process_racing_csv(file):
    try:
        with open(file, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for r in reader:
                d = parse_date({
                    "date": r.get("Date")
                    or r.get("date")
                    or r.get("Day")
                })

                if not d:
                    continue

                race = (
                    r.get("Race")
                    or r.get("Event")
                    or r.get("Meeting")
                )

                winner = (
                    r.get("Winner")
                    or r.get("Horse")
                    or r.get("Runner")
                )

                if race and winner:
                    add_event(
                        d,
                        "Horse Racing",
                        f"{winner.strip()} won the {race.strip()}"
                    )

    except Exception as e:
        print("CSV error:", file, e)

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

    try:
        hs = int(data.get("home_score"))
        as_ = int(data.get("away_score"))
    except:
        return

    home = data.get("home_team")
    away = data.get("away_team")

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
# AFL (FIXED WITH HIGH STATS)
# -----------------------
def process_afl_file(file):
    data = load_json_safe(file)
    if not isinstance(data, list):
        return

    matches = {}

    for row in data:
        d = parse_date(row)
        if not d:
            continue

        home = row.get("home_team") or row.get("played_for")
        away = row.get("away_team") or row.get("played_against")

        if not home or not away:
            continue

        match_id = row.get("match_id") or f"{d}_{home}_{away}"

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

        # SCORE
        if hs > as_:
            text = f"{m['home']} {hs} defeated {m['away']} {as_}"
        else:
            text = f"{m['away']} {as_} defeated {m['home']} {hs}"

        # 🔥 HIGH STATS
        standout = []

        for p in m["players"]:
            name = p.get("player")

            try:
                goals = int(p.get("G") or 0)
                disposals = int(p.get("D") or 0)
                kicks = int(p.get("K") or 0)
            except:
                continue

            if goals >= 5:
                standout.append(f"{name} {goals}g")
            elif disposals >= 30:
                standout.append(f"{name} {disposals}d")
            elif kicks >= 25:
                standout.append(f"{name} {kicks}k")

        if standout:
            text += " — " + ", ".join(standout)

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
# GENERIC (NRL ETC)
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
