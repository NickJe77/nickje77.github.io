import json
from pathlib import Path
import unicodedata
import re

print("BUILDING TENNIS PLAYERS (2025+ ONLY)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
PLAYER_DIR = BASE / "players"

PLAYER_DIR.mkdir(parents=True, exist_ok=True)


def slug(name):
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"\s+", "-", name)


all_matches = []

# 🔥 ONLY LOAD 2025+
for file in MATCH_DIR.glob("*.json"):
    try:
        year = int(file.stem)
    except:
        continue

    if year < 2025:
        continue  # 🚫 DO NOT TOUCH OLD DATA

    try:
        data = json.load(open(file))
    except:
        continue

    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict):
        matches = data.get("matches", [])
    else:
        continue

    if not matches:
        print(f"{year} missing")
        continue

    print(f"{year} done ({len(matches)} matches)")
    all_matches.extend(matches)

print(f"\nTOTAL MATCHES: {len(all_matches)}")


players = {}

for m in all_matches:
    p1 = m.get("player1")
    p2 = m.get("player2")

    if not p1 or not p2:
        continue

    players.setdefault(p1, []).append(m)
    players.setdefault(p2, []).append(m)


index = []

for name, matches in players.items():
    s = slug(name)

    with open(PLAYER_DIR / f"{s}.json", "w") as f:
        json.dump({
            "name": name,
            "matches": matches
        }, f, indent=2)

    index.append(name)

print(f"Saved {len(players)} players")


with open(PLAYER_DIR / "index.json", "w") as f:
    json.dump(sorted(index), f, indent=2)

print("Index built")
