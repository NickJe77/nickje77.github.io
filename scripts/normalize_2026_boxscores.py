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
    "Washington Nationals":"WSH"
}

# =========================================================
# SAFE GET
# =========================================================

def safe(v, default=""):

    if v is None:
        return default

    return v

# =========================================================
# CONVERT
# =========================================================

files = glob.glob(f"{BOX_DIR}/*.json")

print(f"FOUND {len(files)} FILES")

for file in files:

    try:

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print(f"FAILED LOAD {file}")
        print(e)
        continue

    # already converted
    if "events" in data:
        print(f"SKIP NORMALIZED {file}")
        continue

    # =====================================================
    # TEAMS
    # =====================================================

    home_obj = data.get("home_team", {})
    away_obj = data.get("away_team", {})

    home_name = safe(home_obj.get("name"))
    away_name = safe(away_obj.get("name"))

    home_code = TEAM_CODES.get(home_name, safe(home_obj.get("code")))
    away_code = TEAM_CODES.get(away_name, safe(away_obj.get("code")))

    # =====================================================
    # BASIC STRUCTURE
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

        "home_score": safe(home_obj.get("score"), 0),
        "away_score": safe(away_obj.get("score"), 0),

        "events": []

    }

    # =====================================================
    # PLAYS
    # =====================================================

    plays = (
        data.get("liveData", {})
        .get("plays", {})
        .get("allPlays", [])
    )

    for p in plays:

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

print("\nDONE")
