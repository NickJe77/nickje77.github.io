import json
from pathlib import Path
from collections import defaultdict

BASE = Path("docs/data/nba")
OUTPUT = BASE / "finals.json"

def norm(s):
    return (s or "").lower()

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
            pass

    return games


def detect_finals(games):

    playoff_games = [g for g in games if is_playoff(g.get("game_type"))]

    playoff_games.sort(key=lambda g: g.get("date",""))

    series = {}

    for g in playoff_games:

        home = g.get("home_team")
        away = g.get("away_team")

        if not home or not away:
            continue

        key = "_".join(sorted([home,away]))

        if key not in series:
            series[key] = {
                "teams":[home,away],
                "wins":defaultdict(int),
                "games":[]
            }

        home_score = int(g.get("home_score",0))
        away_score = int(g.get("away_score",0))

        winner = home if home_score > away_score else away

        series[key]["wins"][winner] += 1
        series[key]["games"].append(g["game_id"])

    finals = None

    for key,data in series.items():

        for team,wins in data["wins"].items():

            if wins == 4:
                finals = {
                    "champion":team,
                    "runner_up":[t for t in data["teams"] if t != team][0],
                    "series":f"4-{data['wins'][data['runner_up']]}" if "runner_up" in data else "",
                    "games":data["games"]
                }

    return finals


def main():

    seasons = sorted(
        [p for p in BASE.iterdir() if p.is_dir()],
        key=lambda x:int(x.name)
    )

    finals_data = []

    for season_path in seasons:

        season = int(season_path.name)

        print("Processing",season)

        games = load_games(season_path)

        finals = detect_finals(games)

        if finals:

            finals_data.append({
                "season":season,
                "champion":finals["champion"],
                "runner_up":finals["runner_up"],
                "series":finals["series"],
                "games":finals["games"]
            })

    with open(OUTPUT,"w") as f:
        json.dump(finals_data,f,indent=2)

    print("Finals file built:",OUTPUT)


if __name__ == "__main__":
    main()
