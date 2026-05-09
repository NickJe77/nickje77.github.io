import os
import json
from glob import glob

BASE = "docs/data/baseball"

BOX_DIR = f"{BASE}/boxscores"
SEASON_DIR = f"{BASE}/seasons"

TEAM_MAP = {
    "ARI":"Arizona Diamondbacks",
    "ATL":"Atlanta Braves",
    "BAL":"Baltimore Orioles",
    "BOS":"Boston Red Sox",
    "CHC":"Chicago Cubs",
    "CHW":"Chicago White Sox",
    "CHA":"Chicago White Sox",
    "CIN":"Cincinnati Reds",
    "CLE":"Cleveland Guardians",
    "COL":"Colorado Rockies",
    "DET":"Detroit Tigers",
    "HOU":"Houston Astros",
    "KC":"Kansas City Royals",
    "KAN":"Kansas City Royals",
    "LAA":"Los Angeles Angels",
    "ANA":"Los Angeles Angels",
    "LAD":"Los Angeles Dodgers",
    "LOS":"Los Angeles Dodgers",
    "MIA":"Miami Marlins",
    "MIL":"Milwaukee Brewers",
    "MIN":"Minnesota Twins",
    "NYM":"New York Mets",
    "NYY":"New York Yankees",
    "ATH":"Oakland Athletics",
    "OAK":"Oakland Athletics",
    "PHI":"Philadelphia Phillies",
    "PIT":"Pittsburgh Pirates",
    "SD":"San Diego Padres",
    "SDP":"San Diego Padres",
    "SEA":"Seattle Mariners",
    "SF":"San Francisco Giants",
    "SFG":"San Francisco Giants",
    "STL":"St Louis Cardinals",
    "TB":"Tampa Bay Rays",
    "TBR":"Tampa Bay Rays",
    "TEX":"Texas Rangers",
    "TOR":"Toronto Blue Jays",
    "WSH":"Washington Nationals",
    "WAS":"Washington Nationals"
}

def team_name(name):
    return TEAM_MAP.get(name, name)

# ---------------------------------------------------
# FIX SINGLE GAME
# ---------------------------------------------------

def repair_game(game):

    # ---------------------------------
    # FIX TEAM STRUCTURE
    # ---------------------------------

    if isinstance(game.get("home_team"), dict):

        ht = game["home_team"]

        game["home_code"] = ht.get("code", "")
        game["home_team"] = ht.get("name", "")
        game["home_score"] = ht.get("score", 0)

    if isinstance(game.get("away_team"), dict):

        at = game["away_team"]

        game["away_code"] = at.get("code", "")
        game["away_team"] = at.get("name", "")
        game["away_score"] = at.get("score", 0)

    game["home_team"] = team_name(game.get("home_team"))
    game["away_team"] = team_name(game.get("away_team"))

    # ---------------------------------
    # FORCE SCORES
    # ---------------------------------

    home_score = 0
    away_score = 0

    try:

        plays = (
            game.get("liveData", {})
            .get("plays", {})
            .get("allPlays", [])
        )

        if plays:

            # ---------------------------------
            # WALK BACKWARDS THROUGH ALL PLAYS
            # ---------------------------------

            for play in reversed(plays):

                result = play.get("result", {})

                hs = result.get("homeScore")
                aw = result.get("awayScore")

                if hs is not None or aw is not None:

                    if hs > home_score:
                        home_score = hs

                    if aw > away_score:
                        away_score = aw

                # ---------------------------------
                # ALSO CHECK PLAY EVENTS
                # ---------------------------------

                for ev in play.get("playEvents", []):

                    details = ev.get("details", {})

                    hs = details.get("homeScore")
                    aw = details.get("awayScore")

                    if hs is not None or aw is not None:

                        if hs > home_score:
                            home_score = hs

                        if aw > away_score:
                            away_score = aw

    except Exception as e:
        print("SCORE ERROR", e)

    game["home_score"] = home_score
    game["away_score"] = away_score
    game["score"] = f"{away_score} - {home_score}"

    return game

# ---------------------------------------------------
# FIX BOXSCORES
# ---------------------------------------------------

for season in os.listdir(BOX_DIR):

    season_path = f"{BOX_DIR}/{season}"

    if not os.path.isdir(season_path):
        continue

    print(f"\n--- FIXING BOXSCORES {season} ---")

    for file in glob(f"{season_path}/*.json"):

        try:

            with open(file, "r", encoding="utf-8") as f:
                game = json.load(f)

            game = repair_game(game)

            with open(file, "w", encoding="utf-8") as f:
                json.dump(game, f, indent=2)

            print("FIXED", file)

        except Exception as e:
            print("FAILED", file, e)

# ---------------------------------------------------
# FIX SEASON FILES
# ---------------------------------------------------

for file in glob(f"{SEASON_DIR}/*.json"):

    try:

        season = os.path.basename(file).replace(".json", "")

        print(f"\n--- FIXING SEASON {season} ---")

        with open(file, "r", encoding="utf-8") as f:
            games = json.load(f)

        fixed_games = []

        for game in games:

            game = repair_game(game)

            gid = (
                game.get("game_id")
                or game.get("id")
                or game.get("gamePk")
                or ""
            )

            game["link"] = (
                f"baseball-game.html?"
                f"game={gid}&season={season}"
            )

            fixed_games.append(game)

        with open(file, "w", encoding="utf-8") as f:
            json.dump(fixed_games, f, indent=2)

        print("FIXED", file)

    except Exception as e:
        print("FAILED", file, e)

print("\nDONE")
