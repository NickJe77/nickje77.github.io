import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("docs/data/afl")
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

PLAYERS_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------
# LOAD ALL PLAYER ROWS
# -------------------------------
def load_rows():
    rows = []

    for file in DATA_DIR.glob("afl_*.json"):
        print("Loading:", file)

        try:
            data = json.loads(file.read_text())
        except:
            continue

        # YOUR FILE = LIST OF PLAYER ROWS
        if isinstance(data, list):
            rows.extend(data)

        # fallback if wrapped
        elif isinstance(data, dict):
            rows.extend(data.get("games", []))

    return rows


# -------------------------------
# BUILD PLAYERS (🔥 FIXED FOR YOUR STRUCTURE)
# -------------------------------
def build_players(rows):
    players = {}

    for r in rows:

        name = r.get("player")   # 🔥 THIS IS THE FIX
        if not name:
            continue

        if name not in players:
            players[name] = {
                "name": name,
                "games": [],
                "career": defaultdict(int),
            }

        entry = {
            "season": r.get("season"),
            "round": r.get("round"),
            "team": r.get("played_for"),
            "opponent": r.get("played_against"),
            "stats": r
        }

        players[name]["games"].append(entry)

        # aggregate stats
        for k, v in r.items():
            if isinstance(v, (int, float)):
                players[name]["career"][k] += v

    return players


# -------------------------------
# SORT
# -------------------------------
def sort_player_games(players):
    def round_key(r):
        return r if isinstance(r, int) else 999

    for p in players.values():
        p["games"] = sorted(
            p["games"],
            key=lambda g: (g["season"], round_key(g["round"]))
        )


# -------------------------------
# SAVE
# -------------------------------
def save_players(players):
    summary = []

    for name, p in players.items():
        slug = name.lower().replace(" ", "-").replace(".", "")

        file_path = PLAYERS_DIR / f"{slug}.json"

        file_path.write_text(json.dumps({
            "name": name,
            "career": dict(p["career"]),
            "games": p["games"]
        }, indent=2))

        summary.append({
            "name": name,
            "slug": slug,
            "games": len(p["games"])
        })

    PLAYERS_JSON.write_text(json.dumps(summary, indent=2))


# -------------------------------
# MAIN
# -------------------------------
def main():
    print("=== AFL PLAYER BUILD ===")

    rows = load_rows()
    print("TOTAL ROWS:", len(rows))

    players = build_players(rows)
    print("TOTAL PLAYERS:", len(players))

    sort_player_games(players)

    save_players(players)

    print("=== DONE ===")


if __name__ == "__main__":
    main()
