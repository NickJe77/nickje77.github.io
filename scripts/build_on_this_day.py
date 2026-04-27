import json
import csv
import re
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY - FIXED NBA + AFL STATS")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

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

    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d %B %Y"]:
        try:
            clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", d)
            return datetime.strptime(clean[:20], fmt)
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
        "text": text
    })

# =======================
# NBA (FIXED PLAYER STATS)
# =======================
for file in BASE.glob("nba/*/*.json"):
    try:
        g = json.loads(file.read_text())
    except:
        continue

    if "players" not in g:
        continue

    d = parse_date(g)
    if not d:
        continue

    home = g.get("home_team")
    away = g.get("away_team")

    try:
        hs = int(g.get("home_score"))
        as_ = int(g.get("away_score"))
    except:
        continue

    if hs > as_:
        add_event(d, "NBA", f"{home} {hs} defeated {away} {as_}")
    else:
        add_event(d, "NBA", f"{away} {as_} defeated {home} {hs}")

    # 🔥 FIXED PLAYER STAT PARSER
    best = None

    for p in g.get("players", []):
        try:
            pts = int(
                p.get("points")
                or p.get("PTS")
                or p.get("pts")
                or p.get("Points")
                or 0
            )

            reb = int(
                p.get("rebounds")
                or p.get("REB")
                or p.get("reb")
                or p.get("Rebounds")
                or 0
            )

            ast = int(
                p.get("assists")
                or p.get("AST")
                or p.get("ast")
                or p.get("Assists")
                or 0
            )

        except:
            continue

        if not best or pts > best["pts"]:
            best = {
                "name": p.get("player") or p.get("name"),
                "pts": pts,
                "reb": reb,
                "ast": ast
            }

    if best:
        add_event(
            d,
            "NBA",
            f"{best['name']} {best['pts']} pts, {best['reb']} reb, {best['ast']} ast"
        )

# =======================
# AFL (PLAYER ROW STRUCTURE)
# =======================
for file in BASE.glob("afl/*.json"):
    try:
        rows = json.loads(file.read_text())
    except:
        continue

    matches = {}

    for r in rows:
        d = parse_date(r)
        if not d:
            continue

        mid = r.get("match_id")
        if not mid:
            continue

        if mid not in matches:
            matches[mid] = {
                "date": d,
                "home": r.get("played_for"),
                "away": r.get("played_against"),
                "hs": r.get("home_points"),
                "as": r.get("away_points"),
                "players": []
            }

        matches[mid]["players"].append(r)

    for m in matches.values():
        d = m["date"]

        try:
            hs = int(m["hs"])
            as_ = int(m["as"])
        except:
            continue

        if hs > as_:
            text = f"{m['home']} {hs} defeated {m['away']} {as_}"
        else:
            text = f"{m['away']} {as_} defeated {m['home']} {hs}"

        top_g = 0
        top_d = 0
        g_player = None
        d_player = None

        for p in m["players"]:
            try:
                g = int(p.get("G") or 0)
                if g > top_g:
                    top_g = g
                    g_player = p.get("player")
            except:
                pass

            try:
                dpos = int(p.get("D") or 0)
                if dpos > top_d:
                    top_d = dpos
                    d_player = p.get("player")
            except:
                pass

        if g_player:
            text += f" — {g_player} {top_g} goals"

        if d_player:
            text += f" — {d_player} {top_d} disposals"

        add_event(d, "AFL", text)

# =======================
# SAVE
# =======================
OUTPUT.write_text(json.dumps(data_out, indent=2))

print("DONE")
print("Days:", len(data_out))
