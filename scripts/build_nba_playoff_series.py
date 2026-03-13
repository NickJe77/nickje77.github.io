import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("docs/data/nba")
PLAYOFF_FILE = DATA_DIR / "playoff-games.json"
OUTPUT_FILE = DATA_DIR / "playoff-series.json"


def normalise_round(game_type):

    g = game_type.lower()

    if "finals" in g and "conference" not in g:
        return "NBA Finals"

    if "conference finals" in g:
        return "Conference Finals"

    if "semifinals" in g:
        return "Conference Semifinals"

    if "first" in g:
        return "First Round"

    return game_type


def load_games():
    with open(PLAYOFF_FILE) as f:
        return json.load(f)


def build_series(games):

    grouped = defaultdict(list)

    for g in games:

        round_name = normalise_round(g["game_type"])

        teams = tuple(sorted([g["home_team"], g["away_team"]]))

        key = (g["season"], round_name, teams)

        grouped[key].append(g)

    series_list = []

    for (season, round_name, teams), games in grouped.items():

        games.sort(key=lambda x: x["date"])

        wins = {teams[0]: 0, teams[1]: 0}

        game_ids = []

        for g in games:

            home = g["home_team"]
            away = g["away_team"]

            hs = int(g["home_score"])
            as_ = int(g["away_score"])

            if hs > as_:
                winner = home
            else:
                winner = away

            if winner in wins:
                wins[winner] += 1

            game_ids.append(g["game_id"])

        team1, team2 = teams
        w1 = wins[team1]
        w2 = wins[team2]

        winner = team1 if w1 > w2 else team2

        series_list.append({

            "season": season,
            "round": round_name,

            "team1": team1,
            "team2": team2,

            "team1_wins": w1,
            "team2_wins": w2,

            "winner": winner,

            "games": game_ids

        })

    return sorted(series_list, key=lambda x: (x["season"], x["round"]))


def main():

    games = load_games()

    series = build_series(games)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(series, f, indent=2)

    print("Created playoff-series.json with", len(series), "series")


if __name__ == "__main__":
    main()
