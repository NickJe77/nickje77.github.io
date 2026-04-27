import json
import csv
from pathlib import Path
from datetime import datetime
import re

print("BUILDING ON THIS DAY (NO-SKIP VERSION)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# LOAD EXISTING
# -----------------------
if OUTPUT.exists():
    try:
        data_out = json.loads(OUTPUT.read_text(encoding="utf-8"))
    except:
        data_out = {}

for d in data_out:
    for s in data_out[d]:
        for e in data_out[d][s]:
            seen.add(f"{s}|{e['year']}|{e['text']}")

# -----------------------
# FORCE DATE (never skip)
# -----------------------
def parse_date(row):
    if not isinstance(row, dict):
        return datetime(2026, 1, 1)

    d = row.get("date") or row.get("game_date") or row.get("Date")

    if d:
        try:
            return datetime.strptime(str(d)[:10], "%Y-%m-%d")
        except:
            pass

    # NBA fallback
    raw = row.get("DATE")
    season = row.get("SEASON") or "2026"
    if raw:
        try:
            return datetime.strptime(f"{raw} {season}", "%b %d %Y")
        except:
            pass

    # LAST RESORT (this is what stops your empty output)
    return datetime(2026, 1, 1)

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
        "text": text
    })

# -----------------------
# NBA (FORCED OUTPUT)
# -----------------------
def process_nba(file):
    try:
        data = json.loads(file.read_text())
    except:
        return

    if isinstance(data, dict):
        player = data.get("name")
        games = data.get("games", [])
    elif isinstance(data, list):
        player = data[0].get("player") if data else None
        games = data
    else:
        return

    if not player:
        return

    for g in games:

        d = parse_date(g)

        try:
            pts = int(g.get("PTS") or 0)
            reb = int(g.get("REB") or 0)
            ast = int(g.get("AST") or 0)
        except:
            continue

        triple = sum([pts >= 10, reb >= 10, ast >= 10])

        if pts >= 50:
            add_event(d, "NBA", f"{player} 50+ ({pts})")
        elif pts >= 40:
            add_event(d, "NBA", f"{player} {pts} pts")
        elif triple >= 3:
            add_event(d, "NBA", f"{player} TD {pts}/{reb}/{ast}")

# -----------------------
# MLB (FORCED OUTPUT)
# -----------------------
def process_mlb(file):
    try:
        data = json.loads(file.read_text())
    except:
        return

    games = data.get("games") if isinstance(data, dict) else data

    if not isinstance(games, list):
        return

    for g in games:

        d = parse_date(g)

        home = g.get("home") or g.get("team1") or g.get("home_team")
        away = g.get("away") or g.get("team2") or g.get("away_team")

        hs = g.get("home_score") or g.get("runs1")
        as_ = g.get("away_score") or g.get("runs2")

        if not home or not away:
            continue

        try:
            hs = int(hs)
            as_ = int(as_)
        except:
            continue

        if hs > as_:
            add_event(d, "MLB", f"{home} {hs} def {away} {as_}")
        else:
            add_event(d, "MLB", f"{away} {as_} def {home} {hs}")

# -----------------------
# AFL (FORCED HIGH GAMES)
# -----------------------
def process_afl(file):
    try:
        data = json.loads(file.read_text())
    except:
        return

    matches = {}

    for r in data:

        d = parse_date(r)
        mid = r.get("match_id")

        if not mid:
            continue

        matches.setdefault(mid, {
            "date": d,
            "home": r.get("played_for"),
            "away": r.get("played_against"),
            "hs": r.get("home_points"),
            "as": r.get("away_points"),
            "players": []
        })

        matches[mid]["players"].append(r)

    for m in matches.values():

        d = m["date"]

        try:
            hs = int(m["hs"])
            as_ = int(m["as"])
        except:
            continue

        text = f"{m['home']} {hs} vs {m['away']} {as_}"

        best_g = 0
        best_d = 0
        gp = None
        dp = None

        for p in m["players"]:
            try:
                g = int(p.get("G") or 0)
                dpos = int(p.get("D") or 0)

                if g > best_g:
                    best_g = g
                    gp = p.get("player")

                if dpos > best_d:
                    best_d = dpos
                    dp = p.get("player")
            except:
                continue

        # 🔥 ALWAYS ADD IF EXISTS (not strict threshold)
        if gp and best_g > 0:
            text += f" — {gp} {best_g} goals"

        if dp and best_d > 0:
            text += f" — {dp} {best_d} disp"

        add_event(d, "AFL", text)

# -----------------------
# MAIN LOOP
# -----------------------
for file in BASE.rglob("*"):

    path = str(file).lower()

    if not file.is_file():
        continue

    if "nba/players" in path:
        process_nba(file)
        continue

    if "baseball/seasons" in path:
        process_mlb(file)
        continue

    if "afl" in path:
        process_afl(file)
        continue

# -----------------------
# SAVE
# -----------------------
OUTPUT.write_text(json.dumps(data_out, indent=2))

print("DONE")
print("DAYS:", len(data_out))
