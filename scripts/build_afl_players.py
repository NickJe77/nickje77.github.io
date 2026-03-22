import json
import re
import shutil
import unicodedata
from pathlib import Path

print("BUILD AFL PLAYERS — FINAL")

DATA_DIR = Path("docs/data/afl")
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_INDEX = DATA_DIR / "players.json"

# -----------------------------
# RESET OUTPUT
# -----------------------------
if PLAYERS_DIR.exists():
    shutil.rmtree(PLAYERS_DIR)

PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

if PLAYERS_INDEX.exists():
    PLAYERS_INDEX.unlink()

# -----------------------------
# HELPERS
# -----------------------------
def clean_name(name):
    name = unicodedata.normalize("NFD", str(name))
    name = name.encode("ascii", "ignore").decode("utf-8")
    return name.strip()

def slugify(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name.strip("-")

def to_int(value):
    try:
        return int(value)
    except:
        try:
            return int(float(value))
        except:
            return 0

def sort_key(game):
    season = to_int(game.get("season", 0))
    round_num = game.get("round")
    if round_num is None:
        round_num = 999
    return (season, to_int(round_num), game.get("team", ""), game.get("opponent", ""))

# -----------------------------
# LOAD ALL AFL SEASON FILES
# -----------------------------
rows = []

season_files = sorted(DATA_DIR.glob("afl_*.json"))

for file in season_files:
    print("Loading:", file)
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                rows.extend(data)
    except Exception as e:
        print("Failed loading", file, e)

print("TOTAL ROWS LOADED:", len(rows))

# -----------------------------
# BUILD PLAYER GAME LOGS
# -----------------------------
players = {}

for row in rows:
    player_name = clean_name(row.get("player", ""))
    if not player_name:
        continue

    slug = slugify(player_name)
    if not slug:
        continue

    if slug not in players:
        players[slug] = {
            "player": player_name,
            "slug": slug,
            "games": [],
            "_seen": set()
        }

    season = to_int(row.get("season", 0))
    round_num = row.get("round")
    team = row.get("played_for", "")
    opponent = row.get("played_against", "")

    # dedupe key
    game_key = (
        player_name,
        season,
        round_num,
        str(team),
        str(opponent),
        to_int(row.get("K", 0)),
        to_int(row.get("HB", 0)),
        to_int(row.get("D", 0)),
        to_int(row.get("M", 0)),
        to_int(row.get("G", 0)),
        to_int(row.get("B", 0)),
        to_int(row.get("T", 0)),
        to_int(row.get("HO", 0)),
        to_int(row.get("GA", 0)),
        to_int(row.get("I50", 0)),
        to_int(row.get("CL", 0)),
        to_int(row.get("CG", 0)),
        to_int(row.get("R50", 0)),
        to_int(row.get("FF", 0)),
        to_int(row.get("FA", 0)),
        to_int(row.get("AF", 0)),
        to_int(row.get("SC", 0)),
    )

    if game_key in players[slug]["_seen"]:
        continue

    players[slug]["_seen"].add(game_key)

    players[slug]["games"].append({
        "season": season,
        "round": round_num,
        "team": team,
        "opponent": opponent,
        "K": to_int(row.get("K", 0)),
        "HB": to_int(row.get("HB", 0)),
        "D": to_int(row.get("D", 0)),
        "M": to_int(row.get("M", 0)),
        "G": to_int(row.get("G", 0)),
        "B": to_int(row.get("B", 0)),
        "T": to_int(row.get("T", 0)),
        "HO": to_int(row.get("HO", 0)),
        "GA": to_int(row.get("GA", 0)),
        "I50": to_int(row.get("I50", 0)),
        "CL": to_int(row.get("CL", 0)),
        "CG": to_int(row.get("CG", 0)),
        "R50": to_int(row.get("R50", 0)),
        "FF": to_int(row.get("FF", 0)),
        "FA": to_int(row.get("FA", 0)),
        "AF": to_int(row.get("AF", 0)),
        "SC": to_int(row.get("SC", 0))
    })

# -----------------------------
# WRITE PLAYER FILES + INDEX
# -----------------------------
index = []

for slug, pdata in sorted(players.items(), key=lambda x: x[1]["player"]):
    games = sorted(pdata["games"], key=sort_key)

    seasons = sorted({g["season"] for g in games if g.get("season") is not None})
    teams = []
    seen_teams = set()

    for g in games:
        t = g.get("team")
        if t and t not in seen_teams:
            seen_teams.add(t)
            teams.append(t)

    out = {
        "player": pdata["player"],
        "slug": slug,
        "seasons": seasons,
        "teams": teams,
        "games": games
    }

    with open(PLAYERS_DIR / f"{slug}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    index.append({
        "player": pdata["player"],
        "slug": slug,
        "seasons": seasons,
        "teams": teams
    })

with open(PLAYERS_INDEX, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("PLAYER FILES WRITTEN:", len(index))
print("INDEX WRITTEN:", PLAYERS_INDEX)
