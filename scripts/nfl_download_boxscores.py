import json, os, sys

season = sys.argv[1]

games = json.load(open(f"docs/data/nfl/raw/{season}_games.json"))

OUT = f"docs/data/nfl/games/{season}"
os.makedirs(OUT, exist_ok=True)

for g in games:

    gid = g["game_id"]

    print("Saving game:", gid)

    game_data = {
        "game_id": gid,
        "home_team": g.get("home_team"),
        "away_team": g.get("away_team"),
        "home_score": g.get("home_score"),
        "away_score": g.get("away_score"),
        "players": []  # 🔥 leave empty for now
    }

    with open(f"{OUT}/{gid}.json", "w") as f:
        json.dump(game_data, f)
