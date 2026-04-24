import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (FINAL – ALL FIXED)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# LOAD
# -----------------------
def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

# -----------------------
# DATE
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
def add_final_event(d, sport, text):
    key = d.strftime("%m-%d")

    data_out.setdefault(key, {})
    data_out[key].setdefault(sport, [])

    data_out[key][sport].append({
        "year": d.year,
        "text": text,
        "sport": sport
    })

# -----------------------
# GENERIC (ALL OTHER SPORTS)
# -----------------------
def process_generic_file(file, sport):

    data = load_json_safe(file)
    if not data:
        return

    rows = data if isinstance(data, list) else data.get("games", [])

    for row in rows:

        if not isinstance(row, dict):
            continue

        d = parse_date(row)
        if not d:
            continue

        match_id = row.get("match_id") or row.get("game_id")
        uid = f"{sport}|{match_id}"

        if uid in seen:
            continue
        seen.add(uid)

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

        add_final_event(d, sport, text)

# -----------------------
# AFL MERGED
# -----------------------
def process_afl_file(file):

    data = load_json_safe(file)
    if not data:
        return

    matches = {}

    for row in data:

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

        uid = f"AFL|{match_id}"
        if uid in seen:
            continue
        seen.add(uid)

        d = m["date"]

        try:
            hs = int(m["hs"])
            as_ = int(m["as"])

            if hs > as_:
                result = f"{m['home']} {hs} defeated {m['away']} {as_}"
            elif as_ > hs:
                result = f"{m['away']} {as_} defeated {m['home']} {hs}"
            else:
                result = f"{m['home']} {hs} drew with {m['away']} {as_}"
        except:
            result = f"{m['home']} vs {m['away']}"

        # top goal kicker
        top_player = None
        top_goals = 0

        for p in m["players"]:
            try:
                g = int(p.get("G"))
                if g > top_goals:
                    top_goals = g
                    top_player = p.get("player")
            except:
                pass

        if top_player and top_goals >= 5:
            result += f" — {top_player} kicked {top_goals} goals"

        add_final_event(d, "AFL", result)

# -----------------------
# NBA MERGED (YOUR STRUCTURE)
# -----------------------
def process_nba_game(file):

    data = load_json_safe(file)
    if not data:
        return

    # skip non-game files
    if "game_id" not in data:
        return

    d_raw = data.get("date")
    if not d_raw:
        return

    try:
        d = datetime.fromisoformat(d_raw.replace("Z",""))
    except:
        return

    game_id = data.get("game_id")
    uid = f"NBA|{game_id}"

    if uid in seen:
        return
    seen.add(uid)

    home = data.get("home_team")
    away = data.get("away_team")
    hs = data.get("home_score")
    as_ = data.get("away_score")

    try:
        hs = int(hs)
        as_ = int(as_)

        if hs > as_:
            result = f"{home} {hs} defeated {away} {as_}"
        elif as_ > hs:
            result = f"{away} {as_} defeated {home} {hs}"
        else:
            result = f"{home} {hs} drew with {away} {as_}"
    except:
        result = f"{home} vs {away}"

    # top scorer
    top_player = None
    top_pts = 0

    for p in data.get("players", []):
        try:
            pts = int(p.get("points"))
            if pts > top_pts:
                top_pts = pts
                top_player = p.get("player")
        except:
            pass

    if top_player and top_pts >= 40:
        result += f" — {top_player} scored {top_pts} points"

    add_final_event(d, "NBA", result)

# -----------------------
# RACING CSV
# -----------------------
def process_racing_csv(file):

    try:
        with open(file, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for r in reader:

                d = r.get("Date") or r.get("date")
                race = r.get("Race") or r.get("race")
                winner = r.get("Winner") or r.get("winner")

                if not d or not race or not winner:
                    continue

                try:
                    dt = datetime.strptime(d.strip().replace(" ", ""), "%d/%m/%Y")
                except:
                    continue

                key = dt.strftime("%m-%d")

                uid = f"RACING|{dt}|{race}|{winner}"
                if uid in seen:
                    continue
                seen.add(uid)

                data_out.setdefault(key, {})
                data_out[key].setdefault("Racing", [])

                text = f"{winner.strip()} won the {race.strip()}"

                data_out[key]["Racing"].append({
                    "year": dt.year,
                    "text": text,
                    "sport": "Racing"
                })

    except Exception as e:
        print("❌ CSV error:", file, e)

# -----------------------
# SPORT DETECT
# -----------------------
def detect_sport(path):
    p = str(path).lower()
    if "nba" in p: return "NBA"
    if "afl" in p: return "AFL"
    if "nrl" in p: return "NRL"
    if "baseball" in p: return "MLB"
    if "tennis" in p: return "Tennis"
    if "golf" in p: return "Golf"
    if "cycling" in p: return "Cycling"
    if "bathurst" in p: return "Motorsport"
    if "f1" in p: return "F1"
    return None

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    if not file.is_file():
        continue

    path = str(file).lower()

    # 1. RACING CSV FIRST
    if file.suffix.lower() == ".csv":
        process_racing_csv(file)
        continue

    # 2. NBA (your structure)
    if "docs/data/nba/" in path and path.endswith(".json"):
        process_nba_game(file)
        continue

    # 3. AFL
    if "docs/data/afl/" in path and path.endswith(".json"):
        process_afl_file(file)
        continue

    # 4. ALL OTHER SPORTS
    if path.endswith(".json"):
        sport = detect_sport(file)
        if sport and sport not in ["NBA", "AFL"]:
            process_generic_file(file, sport)

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
print("Days built:", len(data_out))
