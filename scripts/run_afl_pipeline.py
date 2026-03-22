import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("docs/data/afl")
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------
# ROUND NORMALISER
# -------------------------------
def clean_round(raw):
    if raw is None:
        return None

    r = str(raw).strip().lower()
    r = r.replace("round", "").strip()

    finals_map = {
        "ef": 25,
        "qf": 26,
        "sf": 27,
        "pf": 28,
        "gf": 29,
        "elimination final": 25,
        "qualifying final": 26,
        "semi final": 27,
        "preliminary final": 28,
        "grand final": 29,
    }

    if r in finals_map:
        return finals_map[r]

    match = re.search(r"\d+", r)
    if match:
        return int(match.group())

    return None


# -------------------------------
# SAFE NUMBER
# -------------------------------
def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0


# -------------------------------
# LOAD ALL GAMES (🔥 FIXED)
# -------------------------------
def load_all_games():
    games = []

    for file in DATA_DIR.glob("afl_*.json"):
        print("Loading:", file)

        try:
            data = json.loads(file.read_text())
        except:
            continue

        # -------------------------------
        # CASE 1: dict format
        # -------------------------------
        if isinstance(data, dict):
            season = int(data.get("season", 0))

            for g in data.get("games", []):
                if not isinstance(g, dict):
                    continue

                g["season"] = season
                g["round"] = clean_round(g.get("round"))
                games.append(g)

        # -------------------------------
        # CASE 2: list format
        # -------------------------------
        elif isinstance(data, list):
            try:
                season = int(file.stem.split("_")[1])
            except:
                season = 0

            for g in data:
                if not isinstance(g, dict):
                    continue

                g["season"] = season
                g["round"] = clean_round(g.get("round"))
                games.append(g)

    return games


# -------------------------------
# DEDUPE GAMES
# -------------------------------
def dedupe_games(games):
    seen = set()
    out = []

    for g in games:
        key = (
            g.get("season"),
            g.get("round"),
            g.get("home_team", {}).get("name"),
            g.get("away_team", {}).get("name"),
            g.get("date"),
        )

        if key in seen:
            continue

        seen.add(key)
        out.append(g)

    return out


# -------------------------------
# BUILD PLAYERS
# -------------------------------
def build_players(games):
    players = {}

    for g in games:
        season = g.get("season")
        rnd = g.get("round")

        home = g.get("home_team", {})
        away = g.get("away_team", {})

        for team, opponent in [(home, away), (away, home)]:
            team_name = team.get("name")
            opp_name = opponent.get("name")

            for p in team.get("players", []):
                name = p.get("name")
                if not name:
                    continue

                if name not in players:
                    players[name] = {
                        "name": name,
                        "games": [],
                        "career": defaultdict(int),
                    }

                entry = {
                    "season": season,
                    "round": rnd,
                    "team": team_name,
                    "opponent": opp_name,
                    "stats": p
                }

                players[name]["games"].append(entry)

                # aggregate stats
                for k, v in p.items():
                    if isinstance(v, (int, float)):
                        players[name]["career"][k] += v

    return players


# -------------------------------
# SORT PLAYER GAMES
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
# SAVE PLAYERS
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
# MAIN PIPELINE
# -------------------------------
def main():
    print("=== AFL PIPELINE START ===")

    games = load_all_games()
    print("TOTAL RAW GAMES:", len(games))

    games = dedupe_games(games)
    print("AFTER DEDUPE:", len(games))

    players = build_players(games)
    print("TOTAL PLAYERS:", len(players))

    sort_player_games(players)

    save_players(players)

    print("=== DONE ===")


if __name__ == "__main__":
    main()
