import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"
OUT.mkdir(exist_ok=True)

players = {}

def clean_name(name):
    if not name:
        return ""

    # remove accents (Doncic vs Dončić)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # remove junk
    name = re.sub(r"[^\w\s.-]", "", name)

    # normalise spacing
    name = re.sub(r"\s+", " ", name).strip()

    return name

def slug(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name

print("🚀 Building NBA player files...")

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

                name = clean_name(raw_name)
                s = slug(name)

                # 🔥 CRITICAL: FORCE MERGE
                if s not in players:
                    players[s] = {
                        "name": name,
                        "slug": s,
                        "games": []
                    }

                players[s]["games"].append({
                    "game_id": game_id,
                    "team": p.get("team"),
                    "opponent": p.get("opponent"),
                    "points": p.get("points", 0),
                    "rebounds": p.get("rebounds", 0),
                    "assists": p.get("assists", 0),
                    "steals": p.get("steals", 0),
                    "blocks": p.get("blocks", 0),
                    "turnovers": p.get("turnovers", 0),
                    "minutes": p.get("minutes")
                })

# ✅ WRITE PLAYER FILES
for s, data in players.items():
    with open(OUT / f"{s}.json", "w") as f:
        json.dump(data, f)

# ✅ BUILD INDEX (UNIQUE)
index = sorted(
    [{"name": p["name"], "slug": p["slug"]} for p in players.values()],
    key=lambda x: x["name"]
)

with open(OUT / "index.json", "w") as f:
    json.dump(index, f)

print(f"✅ Built {len(players)} players")
