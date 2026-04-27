import json
import csv
import re
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY - RESTORED FULL BUILDER")

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

# -----------------------
# ADD EVENT
# -----------------------
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
# NBA - YOUR ACTUAL STRUCTURE
# docs/data/nba/YYYY/game.json
# -----------------------
def process_nba_boxscore(file):
    data = load_json_safe(file)
    if not isinstance(data, dict):
        return

    if "players" not in data:
        return

    d = parse_date(data)
    if not d:
        return

    home = data.get("home_team")
    away = data.get("away_team")
    hs = data.get("home_score")
    as_ = data.get("away_score")

    if home and away and hs is not None and as_ is not None:
        try:
            hs = int(hs)
            as_ = int(as_)
            if hs > as_:
                add_event(d, "NBA", f"{home} {hs} defeated {away} {as_}")
            elif as_ > hs:
                add_event(d, "NBA", f"{away} {as_} defeated {home} {hs}")
            else:
                add_event(d, "NBA", f"{home} {hs} drew with {away} {as_}")
        except:
            pass

    best_player = None
    best_pts = -1
    best_reb = 0
    best_ast = 0

    for p in data.get("players", []):
        if not isinstance(p, dict):
            continue

        try:
            pts = int(p.get("points") or p.get("PTS") or 0)
            reb = int(p.get("rebounds") or p.get("REB") or 0)
            ast = int(p.get("assists") or p.get("AST") or 0)
        except:
            continue

        if pts > best_pts:
            best_pts = pts
            best_reb = reb
            best_ast = ast
            best_player = p.get("player") or p.get("name")

    if best_player and best_pts >= 30:
        add_event(
            d,
            "NBA",
            f"{best_player} had {best_pts} points, {best_reb} rebounds and {best_ast} assists"
        )

# -----------------------
# AFL - PLAYER ROW STRUCTURE
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

    for match_id, m in matches.items():
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
            if m["home"] and m["away"]:
                text = f"{m['home']} vs {m['away']}"
            else:
                continue

        top_goals_player = None
        top_goals = 0
        top_disp_player = None
        top_disp = 0

        for p in m["players"]:
            try:
                g = int(p.get("G") or 0)
                if g > top_goals:
                    top_goals = g
                    top_goals_player = p.get("player")
            except:
                pass

            try:
                disp = int(p.get("D") or 0)
                if disp > top_disp:
                    top_disp = disp
                    top_disp_player = p.get("player")
            except:
                pass

        extras = []

        if top_goals_player and top_goals >= 5:
            extras.append(f"{top_goals_player} kicked {top_goals} goals")

        if top_disp_player and top_disp >= 30:
            extras.append(f"{top_disp_player} had {top_disp} disposals")

        if extras:
            text += " — " + " — ".join(extras)

        add_event(d, "AFL", text)

# -----------------------
# NRL / OTHER GENERIC JSON
# -----------------------
def process_generic_file(file, sport):
    data = load_json_safe(file)
    if not data:
        return

    rows = data if isinstance(data, list) else data.get("games", [])

    if not isinstance(rows, list):
        return

    for row in rows:
        if not isinstance(row, dict):
            continue

        d = parse_date(row)
        if not d:
            continue

        home = (
            row.get("home_team")
            or row.get("home")
            or row.get("team")
            or row.get("played_for")
        )

        away = (
            row.get("away_team")
            or row.get("away")
            or row.get("opponent")
            or row.get("played_against")
        )

        hs = (
            row.get("home_score")
            or row.get("home_points")
            or row.get("team_score")
        )

        as_ = (
            row.get("away_score")
            or row.get("away_points")
            or row.get("opponent_score")
        )

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
# RACING CSV
# -----------------------
def process_racing_csv(file):
    try:
        with open(file, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for r in reader:
                d = parse_date({
                    "date": r.get("Date") or r.get("date")
                })

                if not d:
                    continue

                race = r.get("Race") or r.get("race") or r.get("Event") or r.get("event")
                winner = r.get("Winner") or r.get("winner") or r.get("Driver") or r.get("driver")

                if not race or not winner:
                    continue

                add_event(d, "Racing", f"{winner.strip()} won the {race.strip()}")

    except Exception as e:
        print("CSV error:", file, e)

# -----------------------
# SPORT DETECT
# -----------------------
def detect_sport(path):
    p = str(path).lower()

    if "/nrl/" in p or "\\nrl\\" in p:
        return "NRL"

    if "/tennis/" in p or "\\tennis\\" in p:
        return "Tennis"

    if "/golf/" in p or "\\golf\\" in p:
        return "Golf"

    if "/cycling/" in p or "\\cycling\\" in p:
        return "Cycling"

    if "/bathurst/" in p or "\\bathurst\\" in p:
        return "Motorsport"

    if "/f1/" in p or "\\f1\\" in p:
        return "F1"

    return None

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):
    if not file.is_file():
        continue

    path = str(file).replace("\\", "/").lower()

    if path.endswith("on_this_day.json"):
        continue

    # CSV racing / cycling / motorsport
    if file.suffix.lower() == ".csv":
        process_racing_csv(file)
        continue

    if file.suffix.lower() != ".json":
        continue

    # NBA real folder: docs/data/nba/YYYY/*.json
    if "/nba/" in path:
        process_nba_boxscore(file)
        continue

    # AFL player-row files
    if "/afl/" in path:
        process_afl_file(file)
        continue

    # Generic sports
    sport = detect_sport(path)
    if sport:
        process_generic_file(file, sport)

# -----------------------
# SORT
# -----------------------
for day in data_out:
    for sport in data_out[day]:
        data_out[day][sport].sort(
            key=lambda x: x.get("year", 0),
            reverse=True
        )

# -----------------------
# SAVE
# -----------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(data_out, indent=2), encoding="utf-8")

print("DONE")
print("Days built:", len(data_out))
print("Sports found:", sorted({sport for day in data_out.values() for sport in day.keys()}))
