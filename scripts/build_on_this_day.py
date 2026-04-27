import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (FINAL – NBA UPGRADED)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# LOAD EXISTING (MERGE)
# -----------------------
if OUTPUT.exists():
    try:
        data_out = json.loads(OUTPUT.read_text(encoding="utf-8"))
        print("Loaded existing file")
    except:
        data_out = {}

for day in data_out:
    for sport in data_out[day]:
        for e in data_out[day][sport]:
            seen.add(f"{sport}|{e['year']}|{e['text']}")

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
# ADD EVENT
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
# NBA (UPGRADED)
# -----------------------
def process_nba_player(file):
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except:
        return

    player = data.get("name")
    if not player:
        return

    for game in data.get("games", []):

        d = parse_date(game)
        if not d:
            continue

        try:
            pts = int(game.get("PTS") or 0)
            reb = int(game.get("REB") or 0)
            ast = int(game.get("AST") or 0)
        except:
            continue

        opp = game.get("OPP") or ""

        triple = sum([
            pts >= 10,
            reb >= 10,
            ast >= 10
        ])

        # 🔥 logic tiers
        if pts >= 50:
            text = f"{player} exploded for {pts} points vs {opp}"
        elif pts >= 40:
            text = f"{player} scored {pts} points vs {opp}"
        elif triple >= 3:
            text = f"{player} recorded a triple-double ({pts}/{reb}/{ast}) vs {opp}"
        else:
            continue

        add_event(d, "NBA", text)

# -----------------------
# MLB (SEASONS)
# -----------------------
def process_mlb(file):
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except:
        return

    for g in data.get("games", []):

        d = parse_date(g)
        if not d:
            continue

        home = g.get("home") or g.get("home_team")
        away = g.get("away") or g.get("away_team")

        hs = g.get("home_score") or g.get("home_runs")
        as_ = g.get("away_score") or g.get("away_runs")

        if not home or not away:
            continue

        try:
            hs = int(hs)
            as_ = int(as_)
        except:
            continue

        if hs > as_:
            text = f"{home} {hs} defeated {away} {as_}"
        else:
            text = f"{away} {as_} defeated {home} {hs}"

        add_event(d, "MLB", text)

# -----------------------
# AFL (GOALS + DISPOSALS)
# -----------------------
def process_afl(file):
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except:
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
            "as": row.get("away_points"),
            "players": []
        })

        matches[mid]["players"].append(row)

    for m in matches.values():

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

        top_goals = 0
        top_goal_player = None
        top_disp = 0
        top_disp_player = None

        for p in m["players"]:
            try:
                g = int(p.get("G") or 0)
                if g > top_goals:
                    top_goals = g
                    top_goal_player = p.get("player")
            except:
                pass

            try:
                dpos = int(p.get("D") or 0)
                if dpos > top_disp:
                    top_disp = dpos
                    top_disp_player = p.get("player")
            except:
                pass

        if top_goal_player and top_goals >= 5:
            text += f" — {top_goal_player} kicked {top_goals} goals"

        if top_disp_player and top_disp >= 30:
            text += f" — {top_disp_player} had {top_disp} disposals"

        add_event(d, "AFL", text)

# -----------------------
# GENERIC (NRL ETC)
# -----------------------
def process_generic(file, sport):
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except:
        return

    rows = data if isinstance(data, list) else data.get("games", [])

    for row in rows:

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

                if race and winner:
                    add_event(dt, "Racing", f"{winner} won the {race}")
    except:
        pass

# -----------------------
# DETECT SPORT
# -----------------------
def detect_sport(path):
    p = str(path).lower()
    if "nrl" in p: return "NRL"
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

    if "nba/players" in path:
        process_nba_player(file)
        continue

    if "baseball/seasons" in path:
        process_mlb(file)
        continue

    if "afl" in path:
        process_afl(file)
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
