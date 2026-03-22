import json
import re
import unicodedata
from pathlib import Path

print("BUILD AFL PLAYERS — FULL (FILES + INDEX + ROUND)")

DATA = Path("docs/data/afl/afl_2026.json")
OUT = Path("docs/data/afl/players")
INDEX = Path("docs/data/afl/players.json")

OUT.mkdir(parents=True, exist_ok=True)

if not DATA.exists():
    raise Exception("❌ afl_2026.json not found")

with open(DATA) as f:
    rows = json.load(f)

players = {}

# -----------------------------
# CLEAN NAME
# -----------------------------
def clean_name(name):
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return name.strip()

def slug(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name


# -----------------------------
# BUILD PLAYER DATA
# -----------------------------
for r in rows:

    name = clean_name(r.get("player", ""))
    if not name:
        continue

    key = slug(name)

    if key not in players:
        players[key] = {
            "player": name,
            "slug": key,
            "games": []
        }

    players[key]["games"].append({
        "season": r.get("season"),
        "round": r.get("round"),  # ✅ INCLUDED

        "team": r.get("played_for"),
        "opponent": r.get("played_against"),

        "K": r.get("K", 0),
        "HB": r.get("HB", 0),
        "D": r.get("D", 0),
        "M": r.get("M", 0),
        "G": r.get("G", 0),
        "B": r.get("B", 0),
        "T": r.get("T", 0),
        "HO": r.get("HO", 0),
        "GA": r.get("GA", 0),
        "I50": r.get("I50", 0),
        "CL": r.get("CL", 0),
        "CG": r.get("CG", 0),
        "R50": r.get("R50", 0),
        "FF": r.get("FF", 0),
        "FA": r.get("FA", 0),
        "AF": r.get("AF", 0),
        "SC": r.get("SC", 0)
    })


# -----------------------------
# WRITE PLAYER FILES
# -----------------------------
index = []

count = 0

for key, pdata in players.items():

    out_file = OUT / f"{key}.json"

    with open(out_file, "w") as f:
        json.dump(pdata, f, indent=2)

    index.append({
        "player": pdata["player"],
        "slug": key
    })

    count += 1


# -----------------------------
# WRITE INDEX FILE
# -----------------------------
index = sorted(index, key=lambda x: x["player"])

with open(INDEX, "w") as f:
    json.dump(index, f, indent=2)


print(f"✅ PLAYER FILES: {count}")
print(f"✅ players.json CREATED")
