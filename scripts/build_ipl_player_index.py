import json
import re
from pathlib import Path

DATA_DIR = Path("docs/data/ipl")
OUT_FILE = DATA_DIR / "player-names.json"

def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

players = set()

# LOOP FILES
for file in DATA_DIR.glob("*_FULL.json"):

    with open(file, "r", encoding="utf-8") as f:
        matches = json.load(f)

    for match in matches:
        for inn in match.get("innings", []):
            for over in inn.get("overs", []):
                for d in over.get("deliveries", []):

                    if "batter" in d:
                        players.add(d["batter"].strip())

                    if "bowler" in d:
                        players.add(d["bowler"].strip())

# BUILD MAP
player_map = {}

for name in sorted(players):
    if not name:
        continue
    slug = slugify(name)
    player_map[name] = slug

# SAVE
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(player_map, f, indent=2)

print(f"Built {len(player_map)} players")
