import json
from pathlib import Path

BASE = Path("docs/data/tennis")
SEASONS_DIR = BASE / "seasons"
OUTPUT = BASE / "history.json"

def normalise_match(m):
    return {
        "tournament": m.get("tournament") or m.get("event") or m.get("tourney_name") or "",
        "surface": m.get("surface") or "",
        "round": m.get("round") or "",
        "date": m.get("date") or "",

        "player1": m.get("player1") or m.get("winner") or m.get("w_name") or "",
        "player2": m.get("player2") or m.get("loser") or m.get("l_name") or "",

        "score": m.get("score") or "",

        "gender": m.get("gender") or ""
    }

history = []

print("REBUILDING TENNIS HISTORY")

for file in sorted(SEASONS_DIR.glob("*.json")):
    print(f"Processing {file.name}")

    try:
        with open(file) as f:
            data = json.load(f)

        # ✅ HANDLE BOTH STRUCTURES
        if isinstance(data, list):
            matches = data
        elif isinstance(data, dict):
            matches = data.get("matches") or data.get("results") or []
        else:
            matches = []

        for m in matches:
            if not isinstance(m, dict):
                continue

            fixed = normalise_match(m)

            # ❌ skip junk rows
            if not fixed["player1"] or not fixed["player2"]:
                continue
            if fixed["player2"].lower() == "info":
                continue
            if fixed["score"].lower() == "info":
                continue

            history.append(fixed)

    except Exception as e:
        print(f"ERROR: {file} -> {e}")

# sort
history.sort(key=lambda x: x.get("date", ""))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT, "w") as f:
    json.dump({"matches": history}, f, indent=2)

print(f"DONE: {len(history)} matches saved")
