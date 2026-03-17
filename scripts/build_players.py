import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"
OUT.mkdir(exist_ok=True)

players = {}

def normalize(name):
    if not name:
        return ""

    # remove accents
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # remove punctuation
    name = re.sub(r"[^\w\s-]", "", name)

    # lowercase + clean spaces
    name = re.sub(r"\s+", " ", name).strip().lower()

    return name

def make_slug(name):
    name = normalize(name)
    return name.replace(" ", "-")

print("🚀 Building players (DEDUP FIX)...")

for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    for game_file in season_dir.glob("*.json"):

        if game_file.name in ["index.json", "games.json"]:
            continue

        try:
            game = json.loads(game_file.read_text())
        except:
            continue

        if not isinstance(game, dict):
            continue

        game_id = game.get("game_id") or game_file.stem

        for side in ["home_players", "away_players"]:

            for p in game.get(side, []):

                raw_name = p.get("name") or p.get("player")
                if not raw_name:
                    continue

                slug = make_slug(raw_name)

                # 🔥 FORCE SINGLE PLAYER ENTRY
                if slug not in players:
                    players[slug] = {
                        "name": raw_name.strip(),  # keep first seen name
                        "slug": slug,
                        "games": []
                    }

                players[slug]["games"].append({
                    "game_id": game_id,
                    "team": p.get("team"),
                    "opponent": p.get("opponent"),
                    "points": p.get("points", 0),
                    "rebounds": p.get("rebounds", 0),
                    "assists": p.get("assists", 0),
                    "steals": p.get("steals", 0),
                    "blocks": p.get("blocks", 0)
                })

# WRITE FILES
for slug, data in players.items():
    with open(OUT / f"{slug}.json", "w") as f:
        json.dump(data, f)

# BUILD INDEX (UNIQUE ONLY)
index = sorted(
    [{"name": p["name"], "slug": p["slug"]} for p in players.values()],
    key=lambda x: x["name"]
)

with open(OUT / "index.json", "w") as f:
    json.dump(index, f)

print(f"✅ Built {len(players)} unique players")
