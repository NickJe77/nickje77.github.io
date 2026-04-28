import pandas as pd
import os
import json

# -------------------------
# PATHS
# -------------------------
DATA_DIR = os.path.expanduser("~/Desktop/NFL")

BASE_DIR = "docs/data/nfl"
SEASON_DIR = f"{BASE_DIR}/seasons"
BOX_DIR = f"{BASE_DIR}/boxscores"

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(BOX_DIR, exist_ok=True)

print("🏈 Loading nflscraPy data...")

# -------------------------
# LOAD FILES
# -------------------------
games = pd.read_csv(f"{DATA_DIR}/BoxScores.csv")  # or GameData.csv
players = pd.read_csv(f"{DATA_DIR}/PlayerStats.csv")

# -------------------------
# CLEAN COLUMN NAMES
# -------------------------
games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

# -------------------------
# REQUIRED COLUMNS CHECK
# -------------------------
print("Games columns:", list(games.columns))
print("Players columns:", list(players.columns))

# -------------------------
# BUILD
# -------------------------
for year in sorted(games["season"].unique()):
    if year < 1970:
        continue

    print(f"\n===== {year} =====")

    year_games = games[games["season"] == year]

    year_dir = f"{BOX_DIR}/{year}"
    os.makedirs(year_dir, exist_ok=True)

    season = []

    for _, g in year_games.iterrows():

        gid = str(g.get("game_id") or g.get("gameid"))

        home = g.get("home_team") or g.get("hometeam")
        away = g.get("away_team") or g.get("awayteam")

        hs = int(g.get("home_score") or g.get("homescore") or 0)
        as_ = int(g.get("away_score") or g.get("awayscore") or 0)

        if hs >= as_:
            winner = f"{home} {hs}"
            loser = f"{away} {as_}"
        else:
            winner = f"{away} {as_}"
            loser = f"{home} {hs}"

        # -------------------------
        # PLAYER FILTER (REAL MATCH)
        # -------------------------
        g_players = players[
            (players["season"] == year) &
            (
                (players["game_id"] == gid) |
                (players.get("gameid") == gid)
            )
        ]

        player_list = g_players.to_dict("records")

        # -------------------------
        # SAVE BOXSCORE
        # -------------------------
        with open(f"{year_dir}/{gid}.json", "w") as f:
            json.dump({
                "game_id": gid,
                "home": home,
                "away": away,
                "players": player_list
            }, f, indent=2)

        season.append({
            "game_id": gid,
            "date": str(g.get("date") or g.get("gamedate") or ""),
            "winner": winner,
            "loser": loser,
            "round": "Regular Season",
            "boxscore_file": f"/data/nfl/boxscores/{year}/{gid}.json"
        })

    # -------------------------
    # SAVE SEASON
    # -------------------------
    with open(f"{SEASON_DIR}/{year}.json", "w") as f:
        json.dump({
            "year": int(year),
            "games": season
        }, f, indent=2)

    print(f"✅ {year} done ({len(season)} games)")

print("🔥 DONE")
