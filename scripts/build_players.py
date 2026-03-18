import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

# 🔥 HARD RESET (NO OLD FILES)
if OUT.exists():
    for f in OUT.glob("*.json"):
        f.unlink()
else:
    OUT.mkdir(parents=True)

players = {}

# ---------- NORMALIZE NAME ----------
def normalize(name):
    if not name:
        return ""

    # remove accents
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # fix "Doncic, Luka"
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"

    # remove suffixes
    name = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", name, flags=re.I)

    # remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # clean spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name


# ---------- CANONICAL KEY (THE FIX) ----------
def get_key(name):
    name = normalize(name).lower()
    parts = name.split()

    if len(parts) == 0:
        return None

    if len(parts) == 1:
        return parts[0]

    first = parts[0]
    last = parts[-1]

    # 🔥 CRITICAL: ignore initials completely
    if len(first) == 1:
        return None

    return f"{first}_{last}"


# ---------- SLUG ----------
def make_slug(first, last):
    return f"{first}-{last}"


print("🚀 Building players (FINAL DEDUP)...")

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

                key = get_key(raw_name)

                # 🔥 SKIP BAD / INITIAL NAMES
                if not key:
                    continue

                first, last = key.split("_")
                slug = make_slug(first, last)

                if key not in players:
                    players[key] = {
                        "name": f"{first.capitalize()} {last.capitalize()}",
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
