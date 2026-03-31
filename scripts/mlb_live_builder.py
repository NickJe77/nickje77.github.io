import requests
import json
from pathlib import Path
from datetime import datetime

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

# MLB id -> Retrosheet-style code map for current teams
TEAM_CODE_MAP = {
    108: "LAA",
    109: "ARI",
    110: "BAL",
    111: "BOS",
    112: "CHN",
    113: "CIN",
    114: "CLE",
    115: "COL",
    116: "DET",
    117: "HOU",
    118: "KCA",
    119: "LAN",
    120: "WAS",
    121: "NYN",
    133: "OAK",
    134: "PIT",
    135: "SDN",
    136: "SEA",
    137: "SFN",
    138: "SLN",
    139: "TBA",
    140: "TEX",
    141: "TOR",
    142: "MIN",
    143: "PHI",
    144: "ATL",
    145: "CHA",
    146: "MIA",
    147: "NYA",
    158: "MIL",
}

def get_team_code(team_obj):
    team_id = team_obj.get("id")
    if team_id in TEAM_CODE_MAP:
        return TEAM_CODE_MAP[team_id]

    abbr = team_obj.get("abbreviation")
    if abbr:
        return abbr.upper()

    code = team_obj.get("teamCode")
    if code:
        return code.upper()

    file_code = team_obj.get("fileCode")
    if file_code:
        return file_code.upper()

    name = (team_obj.get("name") or "")[:3].upper()
    return name

def encode_result(play):
    result = play.get("result", {})
    event = (result.get("event") or "").lower()

    if "home run" in event:
        return "HR"
    if "strikeout" in event:
        return "K"
    if "walk" in event:
        return "W"
    if "single" in event:
        return "S"
    if "double" in event:
        return "D"
    if "triple" in event:
        return "T"
    if "ground" in event:
        return "43"
    if "fly" in event:
        return "F8"
    if "line" in event:
        return "L8"
    if "pop" in event:
        return "P2"

    return "O"

def get_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS, timeout=60).json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g.get("gameType") not in ["R", "P"]:
                continue

            home_team = g["teams"]["home"]["team"]
            away_team = g["teams"]["away"]["team"]

            home_code = get_team_code(home_team)
            away_code = get_team_code(away_team)

            # Retrosheet-style: HOMECODE + YYYYMMDD + DH number
            dh_num = "0"

            games.append({
                "gamePk": g["gamePk"],
                "date": g["gameDate"][:10],
                "home_code": home_code,
                "away_code": away_code,
                "game_id": f"{home_code}{g['gameDate'][:10].replace('-', '')}{dh_num}"
            })

    return games

def build_game(game):
    url = f"{BASE}/game/{game['gamePk']}/playByPlay"
    data = requests.get(url, headers=HEADERS, timeout=60).json()

    events = []

    for play in data.get("allPlays", []):
        about = play.get("about", {})
        matchup = play.get("matchup", {})

        inning = str(about.get("inning", ""))
        half = "0" if about.get("halfInning") == "top" else "1"
        batter = str(matchup.get("batter", {}).get("id", "unknown"))
        encoded = encode_result(play)

        events.append([
            "play",
            inning,
            half,
            batter,
            "00",
            "",
            encoded
        ])

    return {
        "game_id": game["game_id"],
        "date": game["date"],
        "season": SEASON,
        "home_code": game["home_code"],
        "away_code": game["away_code"],
        "home_team": game["home_code"],
        "away_team": game["away_code"],
        "events": events
    }

print("BUILDING LIVE MLB DATA...")

games = get_games()

for g in games:
    try:
        game_data = build_game(g)
        out_file = OUTPUT_DIR / f"{game_data['game_id']}.json"

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(game_data, f, separators=(",", ":"))

        print(f"Saved {game_data['game_id']}")
    except Exception as e:
        print(f"Error {g['gamePk']}: {e}")

print("DONE")
