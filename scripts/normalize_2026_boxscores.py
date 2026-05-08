
import os
import json
import glob

BASE = "docs/data/baseball"

BOX_DIR = f"{BASE}/boxscores/2026"

# =========================================================
# TEAM CODES
# =========================================================

TEAM_CODES = {

    "Arizona Diamondbacks":"ARI",
    "Atlanta Braves":"ATL",
    "Baltimore Orioles":"BAL",
    "Boston Red Sox":"BOS",
    "Chicago Cubs":"CHC",
    "Chicago White Sox":"CHW",
    "Cincinnati Reds":"CIN",
    "Cleveland Guardians":"CLE",
    "Colorado Rockies":"COL",
    "Detroit Tigers":"DET",
    "Houston Astros":"HOU",
    "Kansas City Royals":"KC",
    "Los Angeles Angels":"LAA",
    "Los Angeles Dodgers":"LAD",
    "Miami Marlins":"MIA",
    "Milwaukee Brewers":"MIL",
    "Minnesota Twins":"MIN",
    "New York Mets":"NYM",
    "New York Yankees":"NYY",
    "Athletics":"ATH",
    "Oakland Athletics":"ATH",
    "Philadelphia Phillies":"PHI",
    "Pittsburgh Pirates":"PIT",
    "San Diego Padres":"SD",
    "Seattle Mariners":"SEA",
    "San Francisco Giants":"SF",
    "St Louis Cardinals":"STL",
    "St. Louis Cardinals":"STL",
    "Tampa Bay Rays":"TB",
    "Texas Rangers":"TEX",
    "Toronto Blue Jays":"TOR",
    "Washington Nationals":"WSH",

    "ARI":"ARI",
    "ATL":"ATL",
    "BAL":"BAL",
    "BOS":"BOS",
    "CHC":"CHC",
    "CHW":"CHW",
    "CIN":"CIN",
    "CLE":"CLE",
    "COL":"COL",
    "DET":"DET",
    "HOU":"HOU",
    "KC":"KC",
    "KAN":"KC",
    "LAA":"LAA",
    "LAD":"LAD",
    "LOS":"LAD",
    "MIA":"MIA",
    "MIL":"MIL",
    "MIN":"MIN",
    "NYM":"NYM",
    "NYY":"NYY",
    "ATH":"ATH",
    "OAK":"ATH",
    "PHI":"PHI",
    "PIT":"PIT",
    "SD":"SD",
    "SDP":"SD",
    "SEA":"SEA",
    "SF":"SF",
    "SFG":"SF",
    "STL":"STL",
    "TB":"TB",
    "TBR":"TB",
    "TEX":"TEX",
    "TOR":"TOR",
    "WSH":"WSH",
    "WSN":"WSH"
}

# =========================================================
# SAFE GET
# =========================================================

def safe(v, default=""):

    if v is None:
        return default

    return v

# =========================================================
# LOAD FILES
# =========================================================

files = glob.glob(f"{BOX_DIR}/*.json")

print(f"FOUND {len(files)} FILES")

# =========================================================
# NORMALIZE
# =========================================================

for file in files:

    try:

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print(f"FAILED LOAD {file}")
        print(e)
        continue

    # already normalized
    if "events" in data and "liveData" not in data:

        print(f"SKIP NORMALIZED {os.path.basename(file)}")
        continue

    try:

        # =====================================================
        # TEAMS
        # =====================================================

        home_raw = data.get("home_team", {})
        away_raw = data.get("away_team", {})

        # ---------------------------------
        # HOME TEAM
        # ---------------------------------

        if isinstance(home_raw, dict):

            home_name = safe(home_raw.get("name"))

            home_code = TEAM_CODES.get(
                home_name,
                safe(home_raw.get("code"))
            )

            home_score = safe(
                home_raw.get("score"),
                0
            )

        else:

            home_name = str(home_raw)

            home_code = TEAM_CODES.get(
                home_name,
                home_name
            )

            home_score = safe(
                data.get("home_score"),
                0
            )

        # ---------------------------------
        # AWAY TEAM
        # ---------------------------------

        if isinstance(away_raw, dict):

            away_name = safe(away_raw.get("name"))

            away_code = TEAM_CODES.get(
                away_name,
                safe(away_raw.get("code"))
            )

            away_score = safe(
                away_raw.get("score"),
                0
            )

        else:

            away_name = str(away_raw)

            away_code = TEAM_CODES.get(
                away_name,
                away_name
            )

            away_score = safe(
                data.get("away_score"),
                0
            )

        # =====================================================
        # OUTPUT STRUCTURE
        # =====================================================

        out = {

            "game_id": str(data.get("game_id", "")),

            "date": data.get("date", ""),

            "season": 2026,

            "home_code": home_code,
            "away_code": away_code,

            "home_team": home_code,
            "away_team": away_code,

            "venue": data.get("venue", ""),

            "home_score": home_score,
            "away_score": away_score,

            "events": []

        }

        # =====================================================
        # MLB API PLAYS
        # =====================================================

        plays = (
            data.get("liveData", {})
            .get("plays", {})
            .get("allPlays", [])
        )

        for p in plays:

            try:

                result = p.get("result", {})
                matchup = p.get("matchup", {})
                about = p.get("about", {})
                count = p.get("count", {})

                batter = (
                    matchup.get("batter", {})
                    .get("id", "")
                )

                inning = about.get("inning", "")

                balls = count.get("balls", 0)
                strikes = count.get("strikes", 0)

                event_type = result.get("eventType", "")
                desc = result.get("description", "")

                out["events"].append([

                    "play",

                    str(inning),

                    "0",

                    str(batter),

                    f"{balls}-{strikes}",

                    event_type,

                    desc

                ])

            except Exception:
                continue

        # =====================================================
        # SAVE
        # =====================================================

        with open(file, "w", encoding="utf-8") as f:

            json.dump(
                out,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(f"NORMALIZED {os.path.basename(file)}")

    except Exception as e:

        print(f"FAILED NORMALIZE {file}")
        print(e)

print("\nDONE")
