import json
from pathlib import Path
from datetime import datetime

print("BUILDING ON THIS DAY (FINAL WORKING VERSION)")

BASE = Path("docs/data")
OUTPUT = BASE / "on_this_day.json"

data_out = {}
seen = set()

# -----------------------
# LOAD EXISTING
# -----------------------
if OUTPUT.exists():
    try:
        data_out = json.loads(OUTPUT.read_text())
    except:
        data_out = {}

for d in data_out:
    for s in data_out[d]:
        for e in data_out[d][s]:
            seen.add(f"{s}|{e['year']}|{e['text']}")

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

# =======================
# NBA (BOXSCORE STRUCTURE)
# =======================
for file in BASE.glob("nba/*/*.json"):

    try:
        g = json.loads(file.read_text())
    except:
        continue

    if "players" not in g:
        continue

    # DATE
    try:
        d = datetime.strptime(g["date"][:10], "%Y-%m-%d")
    except:
        continue

    home = g.get("home_team")
    away = g.get("away_team")

    hs = g.get("home_score")
    as_ = g.get("away_score")

    if not home or not away:
        continue

    # RESULT (ONLY IF VALID)
    try:
        hs = int(hs)
        as_ = int(as_)
    except:
        continue

    if hs > as_:
        add_event(d, "NBA", f"{home} {hs} def {away} {as_}")
    else:
        add_event(d, "NBA", f"{away} {as_} def {home} {hs}")

    # 🔥 TOP PLAYER (ALWAYS ADD — UNIQUE STRING)
    best_pts = -1
    best_player = None
    best_reb = 0
    best_ast = 0

    for p in g.get("players", []):
        try:
            pts = int(p.get("points") or 0)
            if pts > best_pts:
                best_pts = pts
                best_player = p.get("player")
                best_reb = int(p.get("rebounds") or 0)
                best_ast = int(p.get("assists") or 0)
        except:
            continue

    if best_player:
        # 🔥 MAKE UNIQUE (includes teams)
        add_event(
            d,
            "NBA",
            f"{best_player} {best_pts} pts, {best_reb} reb, {best_ast} ast ({home} vs {away})"
        )

# =======================
# MLB (BOXSCORES ONLY)
# =======================
for file in BASE.glob("baseball/boxscores/*/*.json"):

    try:
        g = json.loads(file.read_text())
    except:
        continue

    # DATE
    try:
        d = datetime.strptime(g["date"], "%Y-%m-%d")
    except:
        continue

    home = g.get("home_team")
    away = g.get("away_team")

    hs = g.get("home_score")
    as_ = g.get("away_score")

    # 🔥 STRICT — ONLY VALID GAMES
    if home is None or away is None:
        continue

    if hs is None or as_ is None:
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

    add_event(d, "MLB", text)

# =======================
# SAVE
# =======================
OUTPUT.write_text(json.dumps(data_out, indent=2))

print("DONE")
print("DAYS:", len(data_out))
