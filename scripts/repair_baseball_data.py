import os
import json
from glob import glob

BASE = "docs/data/baseball"

SEASON_DIR = f"{BASE}/seasons"
BOXSCORE_DIR = f"{BASE}/boxscores"

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
    "NEW":"New York Yankees",
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

VENUE_MAP = {
    "ANA01":"Angel Stadium",
    "ATL02":"Truist Park",
    "BAL12":"Oriole Park at Camden Yards",
    "BOS07":"Fenway Park",
    "CHI11":"Wrigley Field",
    "CHI12":"Guaranteed Rate Field",
    "CIN08":"Great American Ball Park",
    "CLE08":"Progressive Field",
    "DEN02":"Coors Field",
    "DET05":"Comerica Park",
    "HOU03":"Minute Maid Park",
    "KAN06":"Kauffman Stadium",
    "LAA01":"Angel Stadium",
    "LOS03":"Dodger Stadium",
    "MIA02":"loanDepot Park",
    "MIL06":"American Family Field",
    "MIN03":"Target Field",
    "NYC20":"Yankee Stadium",
    "NYC17":"Citi Field",
    "OAK01":"Oakland Coliseum",
    "PHI13":"Citizens Bank Park",
    "PIT08":"PNC Park",
    "SAN01":"Petco Park",
    "SEA03":"T-Mobile Park",
    "SFO03":"Oracle Park",
    "STL10":"Busch Stadium",
    "STP01":"Tropicana Field",
    "TEX05":"Globe Life Field",
    "TOR02":"Rogers Centre",
    "WAS11":"Nationals Park"
}

def clean_team(name):
    if not name:
        return name
    return TEAM_MAP.get(name, name)

def clean_venue(name):
    if not name:
        return name
    return VENUE_MAP.get(name, name)

# ---------------------------------------------------
# FIX SEASON FILES
# ---------------------------------------------------

season_files = glob(f"{SEASON_DIR}/*.json")

for file in season_files:

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False

        for game in data:

            # ----------------------------------------
            # FLATTEN TEAM STRUCTURE
            # ----------------------------------------

            if isinstance(game.get("home_team"), dict):

                ht = game["home_team"]

                game["home_team"] = ht.get("name", "")
                game["home_code"] = ht.get("code", "")
                game["home_score"] = ht.get("score", 0)

                changed = True

            if isinstance(game.get("away_team"), dict):

                at = game["away_team"]

                game["away_team"] = at.get("name", "")
                game["away_code"] = at.get("code", "")
                game["away_score"] = at.get("score", 0)

                changed = True

            # ----------------------------------------
            # ROOT LEVEL SCORES
            # ----------------------------------------

            if "home_score" not in game:
                game["home_score"] = 0

            if "away_score" not in game:
                game["away_score"] = 0

            # TRY LINESCORE FIRST

            linescore = game.get("liveData", {}).get("linescore", {})
            teams = linescore.get("teams", {})

            home = teams.get("home", {})
            away = teams.get("away", {})

            if isinstance(home, dict) and "runs" in home:
                game["home_score"] = home["runs"]

            if isinstance(away, dict) and "runs" in away:
                game["away_score"] = away["runs"]

            # FALLBACK TO LAST PLAY SCORE

            if game["home_score"] == 0 and game["away_score"] == 0:

                all_plays = (
                    game.get("liveData", {})
                    .get("plays", {})
                    .get("allPlays", [])
                )

                if all_plays:

                    last_play = all_plays[-1]

                    result = last_play.get("result", {})

                    hs = result.get("homeScore")
                    aws = result.get("awayScore")

                    if hs is not None:
                        game["home_score"] = hs

                    if aws is not None:
                        game["away_score"] = aws

            # ----------------------------------------
            # SCORE STRING
            # ----------------------------------------

            game["score"] = (
                f"{game['away_score']} - "
                f"{game['home_score']}"
            )

            # ----------------------------------------
            # TEAM NAMES
            # ----------------------------------------

            if "home_team" in game:
                game["home_team"] = clean_team(game["home_team"])

            if "away_team" in game:
                game["away_team"] = clean_team(game["away_team"])

            if "home" in game:
                game["home"] = clean_team(game["home"])

            if "away" in game:
                game["away"] = clean_team(game["away"])

            # ----------------------------------------
            # VENUE
            # ----------------------------------------

            if "venue" in game:
                game["venue"] = clean_venue(game["venue"])

            # ----------------------------------------
            # GAME ID
            # ----------------------------------------

            if "game_id" not in game:

                gid = (
                    game.get("id")
                    or game.get("gamePk")
                    or game.get("pk")
                )

                if gid:
                    game["game_id"] = str(gid)

            # ----------------------------------------
            # LINK
            # ----------------------------------------

            season = os.path.basename(file).replace(".json", "")

            if game.get("game_id"):

                game["link"] = (
                    f"baseball-game.html?"
                    f"game={game['game_id']}"
                    f"&season={season}"
                )

            changed = True

        if changed:

            with open(file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"FIXED: {file}")

    except Exception as e:
        print(f"FAILED: {file} -> {e}")

# ---------------------------------------------------
# FIX BOXSCORES
# ---------------------------------------------------

for season in os.listdir(BOXSCORE_DIR):

    season_path = f"{BOXSCORE_DIR}/{season}"

    if not os.path.isdir(season_path):
        continue

    for file in glob(f"{season_path}/*.json"):

        try:
            with open(file, "r", encoding="utf-8") as f:
                game = json.load(f)

            changed = False

            # ----------------------------------------
            # FLATTEN TEAM STRUCTURE
            # ----------------------------------------

            if isinstance(game.get("home_team"), dict):

                ht = game["home_team"]

                game["home_team"] = ht.get("name", "")
                game["home_code"] = ht.get("code", "")
                game["home_score"] = ht.get("score", 0)

                changed = True

            if isinstance(game.get("away_team"), dict):

                at = game["away_team"]

                game["away_team"] = at.get("name", "")
                game["away_code"] = at.get("code", "")
                game["away_score"] = at.get("score", 0)

                changed = True

            # ----------------------------------------
            # ROOT LEVEL SCORES
            # ----------------------------------------

            if "home_score" not in game:
                game["home_score"] = 0

            if "away_score" not in game:
                game["away_score"] = 0

            # TRY LINESCORE FIRST

            linescore = game.get("liveData", {}).get("linescore", {})
            teams = linescore.get("teams", {})

            home = teams.get("home", {})
            away = teams.get("away", {})

            if isinstance(home, dict) and "runs" in home:
                game["home_score"] = home["runs"]

            if isinstance(away, dict) and "runs" in away:
                game["away_score"] = away["runs"]

            # FALLBACK TO LAST PLAY SCORE

            if game["home_score"] == 0 and game["away_score"] == 0:

                all_plays = (
                    game.get("liveData", {})
                    .get("plays", {})
                    .get("allPlays", [])
                )

                if all_plays:

                    last_play = all_plays[-1]

                    result = last_play.get("result", {})

                    hs = result.get("homeScore")
                    aws = result.get("awayScore")

                    if hs is not None:
                        game["home_score"] = hs

                    if aws is not None:
                        game["away_score"] = aws

            # ----------------------------------------
            # SCORE STRING
            # ----------------------------------------

            game["score"] = (
                f"{game['away_score']} - "
                f"{game['home_score']}"
            )

            # ----------------------------------------
            # TEAM NAMES
            # ----------------------------------------

            for field in [
                "home_team",
                "away_team",
                "home",
                "away"
            ]:
                if field in game:
                    game[field] = clean_team(game[field])

            # ----------------------------------------
            # VENUE
            # ----------------------------------------

            if "venue" in game:
                game["venue"] = clean_venue(game["venue"])

            # ----------------------------------------
            # GAME ID
            # ----------------------------------------

            if "game_id" not in game:

                gid = (
                    game.get("id")
                    or game.get("gamePk")
                    or game.get("pk")
                )

                if gid:
                    game["game_id"] = str(gid)

            changed = True

            if changed:

                with open(file, "w", encoding="utf-8") as f:
                    json.dump(game, f, indent=2)

                print(f"FIXED: {file}")

        except Exception as e:
            print(f"FAILED: {file} -> {e}")

print("\nBASEBALL DATA REPAIR COMPLETE")
