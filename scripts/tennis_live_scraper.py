import json
import re
from pathlib import Path

FILES = [
    "docs/data/tennis/matches/2025.json",
    "docs/data/tennis/matches/2026.json"
]

# -------------------------
def clean_name(name):
    if not name:
        return ""

    # remove seeds
    name = re.sub(r"\(.*?\)", "", name)

    # remove dots
    name = name.replace(".", "")

    return name.strip()

# -------------------------
def fix_surface(s):
    return s if s else "Hard"

# -------------------------
def fix_round(r):

    if not r:
        return "R32"

    r = r.lower()

    # ❌ remove garbage like "Osaka N. (7)"
    if any(x in r for x in ["(", ")"]):
        return "R32"

    if r in ["f", "final"]:
        return "F"
    if "semi" in r:
        return "SF"
    if "quarter" in r:
        return "QF"
    if "16" in r:
        return "R16"
    if "32" in r:
        return "R32"

    return "R32"

# -------------------------
def fix_score(score):

    if not score:
        return ""

    parts = score.split()
    fixed = []

    for p in parts:

        if "-" not in p:
            continue

        a, b = p.split("-")

        # Fix broken tiebreaks (67 → 6(7))
        if len(b) > 1:
            fixed.append(f"{a}-{b[0]}({b[1:]})")
        else:
            fixed.append(p)

    return " ".join(fixed)

# -------------------------
for file in FILES:

    path = Path(file)

    if not path.exists():
        continue

    data = json.loads(path.read_text())

    fixed = []

    for m in data:

        tournament = (m.get("tournament") or "").strip()
        p1 = clean_name(m.get("player1"))
        p2 = clean_name(m.get("player2"))

        if not tournament or not p1 or not p2:
            continue

        fixed.append({
            "tournament": tournament,
            "surface": fix_surface(m.get("surface")),
            "round": fix_round(m.get("round")),
            "player1": p1,
            "player2": p2,
            "score": fix_score(m.get("score")),
            "date": m.get("date"),
            "gender": m.get("gender")
        })

    path.write_text(json.dumps(fixed, indent=2))

print("✅ FIXED TENNIS DATA (2025 & 2026)")
