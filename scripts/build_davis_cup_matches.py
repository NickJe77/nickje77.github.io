import json
from pathlib import Path
from datetime import datetime

BASE = Path("docs/data/tennis/seasons")

print("🏆 Building Davis Cup matches (INCLUDING DOUBLES)")

def parse_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except:
        return datetime(1900,1,1)

def detect_match_type(match):
    players = match.get("players", [])

    # CASE 1: 4 players
    if isinstance(players, list) and len(players) == 4:
        return "Doubles"

    # CASE 2: "A/B"
    if isinstance(players, list) and len(players) == 2:
        if "/" in players[0] or "/" in players[1]:
            return "Doubles"
        return "Singles"

    # CASE 3: team1 / team2
    if match.get("team1") and match.get("team2"):
        if len(match["team1"]) == 2 and len(match["team2"]) == 2:
            return "Doubles"

    return None

for file in BASE.glob("*.json"):

    print(f"Processing {file.name}")

    with open(file) as f:
        data = json.load(f)

    # handle both formats
    if isinstance(data, list):
        matches_source = data
        output_container = {}
    else:
        matches_source = data.get("matches", [])
        output_container = data

    matches_out = []

    for match in matches_source:

        event = str(match.get("event", "")).lower()

        if "davis cup" not in event:
            continue

        match_type = detect_match_type(match)

        if not match_type:
            continue

        # normalize players for output
        players = match.get("players", [])

        if match_type == "Doubles" and match.get("team1"):
            players = match["team1"] + match["team2"]

        matches_out.append({
            "date": match.get("date", ""),
            "event": match.get("event", ""),
            "round": match.get("round", ""),
            "surface": match.get("surface", ""),
            "score": match.get("score", ""),
            "players": players,
            "winner": match.get("winner", ""),
            "match_type": match_type
        })

    matches_out.sort(
        key=lambda x: parse_date(x.get("date","")),
        reverse=True
    )

    if isinstance(data, list):
        output_container = {
            "matches": data,
            "davis_cup_matches": matches_out
        }
    else:
        output_container["davis_cup_matches"] = matches_out

    with open(file, "w") as f:
        json.dump(output_container, f, indent=2)

    print(f"✅ Saved {len(matches_out)} matches for {file.name}")

print("🎾 DONE")
