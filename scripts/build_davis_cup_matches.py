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

for file in BASE.glob("*.json"):

    print(f"Processing {file.name}")

    with open(file) as f:
        data = json.load(f)

    # -------------------------
    # HANDLE BOTH FORMATS
    # -------------------------
    if isinstance(data, list):
        matches_source = data
        output_container = {}   # we’ll wrap output safely
    elif isinstance(data, dict):
        matches_source = data.get("matches", [])
        output_container = data
    else:
        print(f"⚠️ Skipping {file.name} (unknown format)")
        continue

    matches_out = []

    for match in matches_source:

        event = str(match.get("event", "")).lower()

        # ONLY DAVIS CUP
        if "davis cup" not in event:
            continue

        players = match.get("players", [])

        # -------------------------
        # DETECT MATCH TYPE
        # -------------------------
        if isinstance(players, list) and len(players) == 2:
            match_type = "Singles"

        elif isinstance(players, list) and len(players) == 4:
            match_type = "Doubles"

        else:
            continue

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

    # -------------------------
    # SORT NEWEST → OLDEST
    # -------------------------
    matches_out.sort(
        key=lambda x: parse_date(x.get("date","")),
        reverse=True
    )

    # -------------------------
    # SAVE SAFELY
    # -------------------------
    if isinstance(data, list):
        # keep original untouched, add new wrapper file format
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
