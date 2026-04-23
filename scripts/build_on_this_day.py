import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (FINAL + PLAYER STATS)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# SAFE JSON LOAD
# -----------------------
def load_json_safe(path):
    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return None
        return json.loads(text)
    except:
        print(f"❌ Bad JSON: {path}")
        return None

# -----------------------
# DATE PARSER
# -----------------------
def parse_date(row):

    if isinstance(row, dict):
        d = (
            row.get("date_iso")
            or row.get("date")
            or row.get("game_date")
            or row.get("match_date")
            or row.get("Date")
            or row.get("gameDate")
        )
    else:
        d = None

    if not d:
        return None

    d = str(d).strip()

    try:
        return datetime.fromisoformat(d.replace("Z", ""))
    except:
        pass

    try:
        return datetime.strptime(d[:10], "%Y-%m-%d")
    except:
        pass

    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(d.replace(" ", "")[:10], fmt)
        except:
            pass

    try:
        if "," in d:
            d = d.split(",", 1)[1].strip()
        d = d.split(",")[0]
        d = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', d)
        return datetime.strptime(d.strip(), "%d %B %Y")
    except:
        pass

    return None

# -----------------------
# SPORT DETECTION
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
# FILTER FILES
# -----------------------
def is_valid_data_file(path):
    p = str(path).lower()
    if "players" in p: return False
    if "index.json" in p: return False
    if "on_this_day.json" in p: return False
    return True

# -----------------------
# EXTRACT ROWS
# -----------------------
def extract_rows(data):
    if isinstance(data, list):
        return data
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
# ADD GAME EVENT (FIXED)
# -----------------------
def add_event(row, sport, d):

    home = row.get("home_team") or row.get("team") or row.get("played_for")
    away = row.get("away_team") or row.get("opponent") or row.get("played_against")

    hs = row.get("home_score") or row.get("team_score") or row.get("home_points")
    as_ = row.get("away_score") or row.get("opponent_score") or row.get("away_points")

    match_id = row.get("match_id") or row.get("game_id")

    if not home or not away:
        return

    try:
        hs = str(hs).replace("–", "").strip()
        as_ = str(as_).replace("–", "").strip()

        hs_i = int(hs)
        as_i = int(as_)

        if hs_i > as_i:
            text = f"{home} {hs_i} defeated {away} {as_i}"
        elif as_i > hs_i:
            text = f"{away} {as_i} defeated {home} {hs_i}"
        else:
            text = f"{home} {hs_i} drew with {away} {as_i}"
    except:
        text = f"{home} vs {away}"

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
# AFL PLAYER STATS
# -----------------------
def add_afl_player_stats(row, d):

    player = row.get("player")
    goals = row.get("G") or row.get("goals")

    if not player or goals is None:
        return

    try:
        goals = int(goals)
    except:
        return

    if goals < 5:
        return

    key = d.strftime("%m-%d")

    data_out.setdefault(key, {})
    data_out[key].setdefault("AFL", [])

    uid = f"AFL|{d}|{player}|{goals}"
    if uid in seen:
        return
    seen.add(uid)

    text = f"{player} kicked {goals} goals"

    data_out[key]["AFL"].append({
        "year": d.year,
        "text": text,
        "sport": "AFL"
    })

# -----------------------
# NBA BOXSCORE PLAYER STATS
# -----------------------
def process_nba_boxscore(file):

    try:
        data = load_json_safe(file)
        if not data:
            return

        d = parse_date(data)
        if not d:
            return

        key = d.strftime("%m-%d")

        data_out.setdefault(key, {})
        data_out[key].setdefault("NBA", [])

        players = (
            data.get("players")
            or data.get("player_stats")
            or data.get("home_players", []) + data.get("away_players", [])
        )

        if not players:
            return

        for p in players:

            name = p.get("name") or p.get("player")
            pts = p.get("points") or p.get("PTS")

            if not name or pts is None:
                continue

            try:
                pts = int(pts)
            except:
                continue

            if pts < 40:
                continue

            uid = f"NBA|{d}|{name}|{pts}"
            if uid in seen:
                continue
            seen.add(uid)

            text = f"{name} scored {pts} points"

            data_out[key]["NBA"].append({
                "year": d.year,
                "text": text,
                "sport": "NBA"
            })

    except Exception as e:
        print("❌ NBA BOXSCORE ERROR:", file, e)

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
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    if not file.is_file():
        continue

    # 🔥 NBA BOXSCORES FIRST
    if "nba" in str(file).lower() and "boxscores" in str(file).lower():
        process_nba_boxscore(file)
        continue

    if file.suffix.lower() == ".csv":
        process_racing_csv(file)
        continue

    if file.suffix.lower() != ".json":
        continue

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

        if sport == "AFL":
            add_afl_player_stats(row, d)

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
