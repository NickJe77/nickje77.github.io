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

    matches_out = []

    for match in data.get("matches", []):

        event = match.get("event", "").lower()

        # ONLY DAVIS CUP
        if "davis cup" not in event:
            continue

        players = match.get("players", [])

        # -------------------------
        # DETECT SINGLES / DOUBLES
        # -------------------------
        if isinstance(players, list) and len(players) == 2:
            match_type = "Singles"

        elif isinstance(players, list) and len(players) == 4:
            match_type = "Doubles"

        else:
            # fallback (skip weird formats)
            continue

        # -------------------------
        # BUILD MATCH OBJECT
        # -------------------------
        new_match = {
            "date": match.get("date", ""),
            "event": match.get("event", ""),
            "round": match.get("round", ""),
            "surface": match.get("surface", ""),
            "score": match.get("score", ""),
            "players": players,
            "winner": match.get("winner", ""),
            "match_type": match_type
        }

        matches_out.append(new_match)

    # -------------------------
    # SORT NEWEST → OLDEST
    # -------------------------
    matches_out.sort(
        key=lambda x: parse_date(x.get("date","")),
        reverse=True
    )

    # -------------------------
    # SAVE BACK
    # -------------------------
    data["davis_cup_matches"] = matches_out

    with open(file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved {len(matches_out)} matches for {file.name}")

print("🎾 DONE")
