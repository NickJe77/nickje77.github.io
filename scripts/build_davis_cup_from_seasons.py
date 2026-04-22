import json
from pathlib import Path
from datetime import datetime

BASE = Path("docs/data/tennis/seasons")
OUT = Path("docs/data/tennis/davis_cup/davis_cup_all.json")

print("🏆 Building Davis Cup dataset from seasons")

def parse_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except:
        return datetime(1900,1,1)

all_matches = []

for file in BASE.glob("*.json"):

    print("Processing", file.name)

    with open(file) as f:
        data = json.load(f)

    matches = data.get("matches", []) if isinstance(data, dict) else data

    for m in matches:

        tournament = str(m.get("tournament","")).lower()

        # detect Davis Cup
        if "davis cup" not in tournament:
            continue

        # detect doubles (your format)
        if "/" in m.get("player1","") or "/" in m.get("player2",""):
            match_type = "Doubles"
        else:
            match_type = "Singles"

        all_matches.append({
            "date": m.get("date",""),
            "tournament": m.get("tournament",""),
            "round": m.get("round",""),
            "player1": m.get("player1",""),
            "player2": m.get("player2",""),
            "winner": m.get("winner",""),
            "score": m.get("score",""),
            "match_type": match_type
        })

# sort newest first
all_matches.sort(key=lambda x: parse_date(x["date"]), reverse=True)

OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(all_matches, f, indent=2)

print("✅ Saved:", len(all_matches), "matches")
