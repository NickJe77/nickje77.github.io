import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

# 🔥 CLEAN START (IMPORTANT)
if OUT.exists():
    for f in OUT.glob("*.json"):
        f.unlink()
else:
    OUT.mkdir(parents=True)

players = {}

# ---------- NORMALIZE ----------
def normalize(name):
    if not name:
        return ""

    # Remove accents
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Handle "Doncic, Luka"
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"

    # Remove suffixes
    name = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", name, flags=re.I)

    # Remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # Clean spacing
    name = re.sub(r"\s+", " ", name).strip()

    return name

# ---------- KEY BUILDER ----------
def build_key(name):
    name = normalize(name).lower()
    parts = name.split()

    if len(parts) == 1:
        return parts[0]

    first = parts[0]
    last = parts[-1]

    # 🔥 IGNORE INITIAL-ONLY FIRST NAMES
    if len(first) == 1:
        return f"*IGNORE*_{last}"

    return f"{first}_{last}"

# ---------- SLUG ----------
def make_slug(name):
    name = normalize(name).lower()
    return name.replace(" ", "-")

print("🚀 Building players (HARD DEDUP)...")

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

                key = build_key(raw_name)

                # 🔥 SKIP BAD INITIAL PLAYERS IF FULL VERSION EXISTS
                if key.startswith("*IGNORE*"):
                    last = key.replace("*IGNORE*_", "")
                    if any(k.endswith(f"_{last}") for k in players):
                        continue

                slug = make_slug(raw_name)

                if key not in players:
                    players[key] = {
                        "name": normalize(raw_name),
                        "slug": slug,
                        "games": []
                    }

                players[key]["games"].append({
                    "game_id": game_id,
                    "team": p.get("team"),
                    "opponent": p.get("opponent"),
                    "points": p.get("points", 0),
                    "rebounds": p.get("rebounds", 0),
                    "assists": p.get("assists", 0),
                    "steals": p.get("steals", 0),
                    "blocks": p.get("blocks", 0)
                })

# ---------- WRITE FILES ----------
for data in players.values():
    with open(OUT / f"{data['slug']}.json", "w") as f:
        json.dump(data, f)

# ---------- INDEX ----------
index = sorted(
    [{"name": p["name"], "slug": p["slug"]} for p in players.values()],
    key=lambda x: x["name"]
)

with open(OUT / "index.json", "w") as f:
    json.dump(index, f)

print(f"✅ Built {len(players)} unique players")
