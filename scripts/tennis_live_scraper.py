import json
from pathlib import Path
import re

FILES = [
    "docs/data/tennis/matches/2025.json",
    "docs/data/tennis/matches/2026.json"
]

def clean_name(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace(".", "").strip()
    return name

def fix_score(score):
    if not score:
        return ""

    parts = score.split()
    fixed = []

    for p in parts:
        if "-" in p:
            a,b = p.split("-")
            if len(b) > 1:
                fixed.append(f"{a}-{b[0]}({b[1:]})")
            else:
                fixed.append(p)

    return " ".join(fixed)

def fix_round(r):
    r = (r or "").lower()

    if "final" in r: return "F"
    if "semi" in r: return "SF"
    if "quarter" in r: return "QF"

    return r.upper() if r else "R32"

for file in FILES:

    path = Path(file)
    data = json.loads(path.read_text())

    for m in data:

        m["player1"] = clean_name(m.get("player1"))
        m["player2"] = clean_name(m.get("player2"))

        m["score"] = fix_score(m.get("score"))

        m["round"] = fix_round(m.get("round"))

        if not m.get("surface"):
            m["surface"] = "Hard"

    path.write_text(json.dumps(data, indent=2))

print("✅ CLEANED DATA")
