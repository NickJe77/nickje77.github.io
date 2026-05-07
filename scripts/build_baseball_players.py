import os
import json
import re
from collections import defaultdict

BASE = "docs/data/baseball"

SEASONS_DIR = f"{BASE}/seasons"
BOX_DIR = f"{BASE}/boxscores"

PLAYERS_DIR = f"{BASE}/players"
INDEX_FILE = f"{BASE}/players.json"

os.makedirs(PLAYERS_DIR, exist_ok=True)

players = defaultdict(lambda: {
    "name": "",
    "slug": "",
    "games": []
})

# -------------------------
# SLUGIFY
# -------------------------

def slugify(name):
    name = name.lower().strip()

    replacements = {
        "á":"a","à":"a","ä":"a","â":"a",
        "é":"e","è":"e","ë":"e","ê":"e",
        "í":"i","ì":"i","ï":"i","î":"i",
        "ó":"o","ò":"o","ö":"o","ô":"o",
        "ú":"u","ù":"u","ü":"u","û":"u",
        "ñ":"n"
    }

    for k,v in replacements.items():
        name = name.replace(k,v)

    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)

    return name

# -------------------------
# SAFE INT
# -------------------------

def safe_int(v):
    try:
        return int(v)
    except:
        return 0

# -------------------------
# LOAD SEASONS
# -------------------------

season_files = sorted([
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

for sf in season_files:

    season = sf.replace(".json", "")

    season_path = os.path.join(SEASONS_DIR, sf)

    print(f"Processing season {season}")

    try:
        with open(season_path, "r", encoding="utf-8") as f:
            games = json.load(f)
    except Exception as e:
        print(f"Failed season {season}: {e}")
        continue

    if not isinstance(games, list):
        continue

    for g in games:

        file_name = (
            g.get("game_file") or
            g.get("filename") or
            g.get("file") or
            ""
        )

        if not file_name:
            continue

        if not file_name.endswith(".json"):
            file_name += ".json"

        box_path = os.path.join(
            BOX_DIR,
            season,
            file_name
        )

        if not os.path.exists(box_path):
            continue

        try:
            with open(box_path, "r", encoding="utf-8") as f:
                box = json.load(f)
        except:
            continue

        date = (
            box.get("date") or
            g.get("date") or
            ""
        )

        home_code = (
            box.get("home_code") or
            g.get("home_code") or
            g.get("home") or
            ""
        )

        away_code = (
            box.get("away_code") or
            g.get("away_code") or
            g.get("away") or
            ""
        )

        home_list = (
            box.get("batters_home") or
            box.get("batting_home") or
            []
        )

        away_list = (
            box.get("batters_away") or
            box.get("batting_away") or
            []
        )

        def process_player(p, is_home):

            name = (
                p.get("name") or
                p.get("fullName") or
                p.get("player") or
                ""
            ).strip()

            if not name:
                return

            slug = slugify(name)

            ab = safe_int(
                p.get("AB") or
                p.get("ab") or
                p.get("atBats")
            )

            hits = safe_int(
                p.get("H") or
                p.get("h") or
                p.get("hits")
            )

            hr = safe_int(
                p.get("HR") or
                p.get("hr") or
                p.get("homeRuns")
            )

            rbi = safe_int(
                p.get("RBI") or
                p.get("rbi")
            )

            runs = safe_int(
                p.get("R") or
                p.get("runs")
            )

            player = players[slug]

            player["name"] = name
            player["slug"] = slug

            player["games"].append({
                "season": season,
                "date": date,
                "team": home_code if is_home else away_code,
                "opponent": away_code if is_home else home_code,
                "AB": ab,
                "H": hits,
                "HR": hr,
                "RBI": rbi,
                "R": runs
            })

        for p in home_list:
            process_player(p, True)

        for p in away_list:
            process_player(p, False)

# -------------------------
# SAVE PLAYERS
# -------------------------

print("Saving player files...")

index = []

for slug, data in players.items():

    out_path = os.path.join(
        PLAYERS_DIR,
        f"{slug}.json"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    index.append({
        "name": data["name"],
        "slug": slug
    })

# -------------------------
# SAVE INDEX
# -------------------------

index = sorted(index, key=lambda x: x["name"])

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2)

print(f"Built {len(players)} player files")
print("Saved players.json")
