import json
from pathlib import Path
from collections import defaultdict

BASE = Path("docs/data/nba")
OUTPUT = BASE / "finals.json"


def is_playoff(game_type):
    if not game_type:
        return False
    return "playoff" in game_type.lower()


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


def detect_finals(games):

    playoff_games = []

    for g in games:
        if is_playoff(g.get("game_type")):
            playoff_games.append(g)

    if not playoff_games:
        return None

    playoff_games.sort(key=lambda g: g.get("date", ""))

    series = {}

    for g in playoff_games:

        home = g.get("home_team")
        away = g.get("away_team")

        if not home or not away:
            continue

        key = "_".join(sorted([home, away]))

        if key not in series:
            series[key] = {
                "teams": [home, away],
                "wins": defaultdict(int),
                "games": [],
                "last_date": ""
            }

        home_score = int(g.get("home_score", 0))
        away_score = int(g.get("away_score", 0))

        winner = home if home_score > away_score else away

        series[key]["wins"][winner] += 1
        series[key]["games"].append(g.get("game_id"))

        date = g.get("date", "")
        if date > series[key]["last_date"]:
            series[key]["last_date"] = date

    finals = None
    latest_date = ""

    for data in series.values():

        for team in list(data["wins"].keys()):

            wins = data["wins"][team]

            if wins == 4:

                runner = [t for t in data["teams"] if t != team][0]
                runner_wins = data["wins"].get(runner, 0)

                if data["last_date"] > latest_date:

                    finals = {
                        "champion": team,
                        "runner_up": runner,
                        "series": f"4-{runner_wins}",
                        "games": data["games"]
                    }

                    latest_date = data["last_date"]

    return finals


def main():

    season_dirs = []

    for p in BASE.iterdir():
        if p.is_dir() and p.name.isdigit():
            season_dirs.append(p)

    season_dirs.sort(key=lambda p: int(p.name))

    finals_output = []

    for season_path in season_dirs:

        season = int(season_path.name)

        print("Scanning season", season)

        games = load_games(season_path)

        finals = detect_finals(games)

        if finals:

            finals_output.append({
                "season": season,
                "champion": finals["champion"],
                "runner_up": finals["runner_up"],
                "series": finals["series"],
                "games": finals["games"]
            })

    with open(OUTPUT, "w") as f:
        json.dump(finals_output, f, indent=2)

    print("Finals file written:", OUTPUT)


if __name__ == "__main__":
    main()
