import json
from pathlib import Path
from datetime import datetime
import csv

print("ON THIS DAY - FULL RECOVERY")

FILE = Path("docs/data/on_this_day.json")
BASE = Path("docs/data")

data = json.loads(FILE.read_text())

# -----------------------
def add(day, sport, year, text):
    data.setdefault(day, {})
    data[day].setdefault(sport, [])

    if not any(e["text"] == text for e in data[day][sport]):
        data[day][sport].append({
            "year": year,
            "text": text
        })

# =======================
# CLEAN MLB JUNK
# =======================
for day in list(data.keys()):
    if "MLB" in data[day]:
        data[day]["MLB"] = [e for e in data[day]["MLB"] if " vs " not in e["text"]]
        if not data[day]["MLB"]:
            del data[day]["MLB"]

# =======================
# NBA STATS FIX
# =======================
for file in BASE.glob("nba/*/*.json"):
    try:
        g = json.loads(file.read_text())
    except:
        continue

    if "players" not in g:
        continue

    try:
        d = datetime.strptime(g["date"][:10], "%Y-%m-%d")
    except:
        continue

    day = d.strftime("%m-%d")
    year = d.year

    if day not in data:
        continue

    best = None
    for p in g.get("players", []):
        try:
            pts = int(p.get("points") or 0)
            if not best or pts > best["pts"]:
                best = {
                    "name": p.get("player"),
                    "pts": pts,
                    "reb": int(p.get("rebounds") or 0),
                    "ast": int(p.get("assists") or 0)
                }
        except:
            continue

    if best:
        text = f"{best['name']} {best['pts']} pts, {best['reb']} reb, {best['ast']} ast"
        add(day, "NBA", year, text)

# =======================
# AFL RESTORE
# =======================
for file in BASE.glob("afl/*.json"):
    try:
        rows = json.loads(file.read_text())
    except:
        continue

    for r in rows:
        try:
            d = datetime.strptime(r["date"][:10], "%Y-%m-%d")
        except:
            continue

        day = d.strftime("%m-%d")
        year = d.year

        home = r.get("played_for")
        away = r.get("played_against")

        hs = r.get("home_points")
        as_ = r.get("away_points")

        if not home or not away:
            continue

        try:
            hs = int(hs)
            as_ = int(as_)
        except:
            continue

        if hs > as_:
            text = f"{home} {hs} def {away} {as_}"
        else:
            text = f"{away} {as_} def {home} {hs}"

        add(day, "AFL", year, text)

# =======================
# NRL RESTORE
# =======================
for file in BASE.glob("nrl/*.json"):
    try:
        rows = json.loads(file.read_text())
    except:
        continue

    for r in rows:
        try:
            d = datetime.strptime(r["date"][:10], "%Y-%m-%d")
        except:
            continue

        day = d.strftime("%m-%d")
        year = d.year

        home = r.get("home_team")
        away = r.get("away_team")

        hs = r.get("home_score")
        as_ = r.get("away_score")

        if not home or not away:
            continue

        try:
            hs = int(hs)
            as_ = int(as_)
        except:
            continue

        if hs > as_:
            text = f"{home} {hs} def {away} {as_}"
        else:
            text = f"{away} {as_} def {home} {hs}"

        add(day, "NRL", year, text)

# =======================
# RACING RESTORE
# =======================
for file in BASE.rglob("*.csv"):
    if "cycling" not in str(file).lower():
        continue

    try:
        with open(file, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    d = datetime.strptime(r["Date"][:10], "%Y-%m-%d")
                except:
                    continue

                day = d.strftime("%m-%d")
                year = d.year

                race = r.get("Race")
                winner = r.get("Winner")

                if race and winner:
                    text = f"{winner} won the {race}"
                    add(day, "Racing", year, text)
    except:
        continue

# =======================
# SAVE
# =======================
FILE.write_text(json.dumps(data, indent=2))

print("DONE - EVERYTHING RESTORED")
