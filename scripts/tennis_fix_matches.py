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

    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace(".", "").strip()

    return name

# -------------------------
def fix_score(score):
    if not score:
        return ""

    parts = score.split()
    fixed = []

    for p in parts:
        if "-" not in p:
            continue

        a,b = p.split("-")

        # handle broken tiebreak like 67 → 6(7)
        if len(b) > 1:
            fixed.append(f"{a}-{b[0]}({b[1:]})")
        else:
            fixed.append(p)

    return " ".join(fixed)

# -------------------------
def fix_round(r):

    r = (r or "").lower()

    if r in ["f","final"]:
        return "F"
    if "semi" in r or r == "sf":
        return "SF"
    if "quarter" in r or r == "qf":
        return "QF"

    if "16" in r:
        return "R16"
    if "32" in r:
        return "R32"
    if "64" in r:
        return "R64"

    return "R32"

# -------------------------
for file in FILES:

    path = Path(file)
    data = json.loads(path.read_text())

    fixed = []

    for m in data:

        tournament = m.get("tournament")
        p1 = clean_name(m.get("player1"))
        p2 = clean_name(m.get("player2"))

        if not tournament or not p1 or not p2:
            continue

        fixed.append({
            "tournament": tournament.strip(),
            "surface": m.get("surface") or "Hard",
            "round": fix_round(m.get("round")),
            "player1": p1,
            "player2": p2,
            "score": fix_score(m.get("score")),
            "date": m.get("date"),
            "gender": m.get("gender")
        })

    path.write_text(json.dumps(fixed, indent=2))

print("✅ 2025 & 2026 NOW MATCH 2024 FORMAT")
