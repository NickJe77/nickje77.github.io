import os
import json
from collections import defaultdict

BASE = "docs/data/nfl"

SEASONS_DIR = f"{BASE}/seasons"
BOXSCORE_DIR = f"{BASE}/boxscores"

PLAYERS_DIR = f"{BASE}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

TEAM_MAP = {
    "ARI":"Arizona Cardinals",
    "ATL":"Atlanta Falcons",
    "BAL":"Baltimore Ravens",
    "BUF":"Buffalo Bills",
    "CAR":"Carolina Panthers",
    "CHI":"Chicago Bears",
    "CIN":"Cincinnati Bengals",
    "CLE":"Cleveland Browns",
    "DAL":"Dallas Cowboys",
    "DEN":"Denver Broncos",
    "DET":"Detroit Lions",
    "GB":"Green Bay Packers",
    "HOU":"Houston Texans",
    "IND":"Indianapolis Colts",
    "JAX":"Jacksonville Jaguars",
    "KAN":"Kansas City Chiefs",
    "KC":"Kansas City Chiefs",
    "LAC":"Los Angeles Chargers",
    "LAR":"Los Angeles Rams",
    "LV":"Las Vegas Raiders",
    "MIA":"Miami Dolphins",
    "MIN":"Minnesota Vikings",
    "NE":"New England Patriots",
    "NO":"New Orleans Saints",
    "NYG":"New York Giants",
    "NYJ":"New York Jets",
    "PHI":"Philadelphia Eagles",
    "PIT":"Pittsburgh Steelers",
    "SEA":"Seattle Seahawks",
    "SF":"San Francisco 49ers",
    "TB":"Tampa Bay Buccaneers",
    "TEN":"Tennessee Titans",
    "WAS":"Washington Commanders"
}

def slugify(name):
    return (
        str(name or "")
        .lower()
        .replace(".", "")
        .replace("'", "")
        .replace(",", "")
        .replace(" ", "-")
    )

players = defaultdict(lambda: {
    "player_id": "",
    "name": "",
    "teams": set(),
    "seasons": set(),
    "games": []
})

player_names = set()

season_files = sorted(os.listdir(SEASONS_DIR))

for season_file in season_files:

    if not season_file.endswith(".json"):
        continue

    season = season_file.replace(".json", "")

    season_path = f"{SEASONS_DIR}/{season_file}"

    try:

        with open(season_path, "r", encoding="utf-8") as f:
            season_data = json.load(f)

    except:
        continue

    games = season_data.get("games", season_data)

    for game in games:

        game_id = (
            game.get("game_id")
            or game.get("id")
        )

        if not game_id:
            continue

        box_path = f"{BOXSCORE_DIR}/{season}/{game_id}.json"

        if not os.path.exists(box_path):
            continue

        try:

            with open(box_path, "r", encoding="utf-8") as f:
                box = json.load(f)

        except:
            continue

        sections = {
            "passing": box.get("passing", []),
            "rushing": box.get("rushing", []),
            "receiving": box.get("receiving", [])
        }

        all_players = []

        for sec_players in sections.values():
            all_players.extend(sec_players)

        teams = list(set([
            (p.get("stats") or {}).get("team", "")
            for p in all_players
            if (p.get("stats") or {}).get("team")
        ]))

        for section_name, section_players in sections.items():

            for p in section_players:

                name = p.get("player")

                if not name:
                    continue

                slug = slugify(name)

                player_names.add(name)

                stats = p.get("stats") or {}

                team_code = stats.get("team", "")

                opponent_code = ""

                for t in teams:
                    if t != team_code:
                        opponent_code = t
                        break

                player_obj = players[slug]

                player_obj["player_id"] = slug
                player_obj["name"] = name

                if team_code:
                    player_obj["teams"].add(team_code)

                player_obj["seasons"].add(int(season))

                obj = {
                    "game_id": game_id,
                    "season": int(season),
                    "date": game.get("date", ""),
                    "team": TEAM_MAP.get(team_code, team_code),
                    "opponent": TEAM_MAP.get(opponent_code, opponent_code),
                    "game_type": (
                        game.get("game_type")
                        or game.get("type")
                        or "Regular Season"
                    ),
                    "section": section_name,
                    "stats": stats
                }

                player_obj["games"].append(obj)

print("Writing NFL player files...")

for slug, data in players.items():

    data["teams"] = sorted(list(data["teams"]))
    data["seasons"] = sorted(list(data["seasons"]))

    data["games"] = sorted(
        data["games"],
        key=lambda x: (
            x.get("season", 0),
            x.get("date", "")
        )
    )

    out_path = f"{PLAYERS_DIR}/{slug}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

index_path = f"{PLAYERS_DIR}/index.json"

with open(index_path, "w", encoding="utf-8") as f:
    json.dump(sorted(player_names), f, indent=2)

print(f"Built {len(players)} NFL player files")
