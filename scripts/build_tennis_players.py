import json
from pathlib import Path
import unicodedata
import re

print("BUILDING TENNIS PLAYERS")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
PLAYER_DIR = BASE / "players"

PLAYER_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# SLUG FUNCTION
# -----------------------------
def slug(name):
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"\s+", "-", name)


# -----------------------------
# LOAD ALL MATCHES
# -----------------------------
all_matches = []

for file in MATCH_DIR.glob("*.json"):
    try:
        data = json.load(open(file))
    except Exception as e:
        print(f"Failed to load {file}: {e}")
        continue

    # ✅ HANDLE BOTH STRUCTURES
    if isinstance(data, dict) and "matches" in data:
        matches = data["matches"]
    elif isinstance(data, list):
        matches = data
    else:
        print(f"Skipping bad format: {file}")
        continue

    if not matches:
        print(f"{file.stem} missing")
        continue

    print(f"{file.stem} done ({len(matches)} matches)")
    all_matches.extend(matches)

print(f"\nTOTAL MATCHES LOADED: {len(all_matches)}")


# -----------------------------
# BUILD PLAYER MAP
# -----------------------------
players = {}

for m in all_matches:
    p1 = m.get("player1")
    p2 = m.get("player2")

    if not p1 or not p2:
        continue

    players.setdefault(p1, []).append(m)
    players.setdefault(p2, []).append(m)


# -----------------------------
# SAVE PLAYER FILES
# -----------------------------
index = []

for name, matches in players.items():
    s = slug(name)

    out = {
        "name": name,
        "matches": matches
    }

    with open(PLAYER_DIR / f"{s}.json", "w") as f:
        json.dump(out, f, indent=2)

    index.append(name)

print(f"Saved {len(players)} players")


# -----------------------------
# BUILD INDEX
# -----------------------------
with open(PLAYER_DIR / "index.json", "w") as f:
    json.dump(sorted(index), f, indent=2)

print("Index built successfully")
