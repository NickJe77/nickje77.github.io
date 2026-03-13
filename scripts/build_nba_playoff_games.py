import json
from pathlib import Path

BASE = Path("docs/data/nba")
OUTPUT = BASE / "playoff-games.json"


def is_playoff(game_type):

    if not game_type:
        return False

    t = game_type.lower()

    if "playoff" in t:
        return True

    if "final" in t:
        return True

    return False


def load_games(season_path):

    index_file = season_path / "index.json"

    if not index_file.exists():
        return []

    with open(index_file) as f:
        index = json.load(f)

    games = []

    for gid in index.get("games", []):

        gfile = season_path / f"{gid}.json"

        if not gfile.exists():
            continue

        try:
            with open(gfile) as f:
                g = json.load(f)
                games.append(g)
        except:
            continue

    return games


def main():

    seasons = []

    for p in BASE.iterdir():

        if p.is_dir() and p.name.isdigit():
            seasons.append(p)

    seasons.sort(key=lambda p:int(p.name))

    playoff_games = []

    for season_path in seasons:

        season = int(season_path.name)

        print("Scanning season",season)

        games = load_games(season_path)

        for g in games:

            if not is_playoff(g.get("game_type")):
                continue

            playoff_games.append({

                "season":season,
                "game_id":g.get("game_id"),
                "date":g.get("date"),
                "home_team":g.get("home_team"),
                "away_team":g.get("away_team"),
                "home_score":g.get("home_score"),
                "away_score":g.get("away_score"),
                "game_type":g.get("game_type")

            })

    with open(OUTPUT,"w") as f:
        json.dump(playoff_games,f,indent=2)

    print("Playoff games written:",OUTPUT)


if __name__ == "__main__":
    main()
