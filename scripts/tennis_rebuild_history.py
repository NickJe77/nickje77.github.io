import json
from pathlib import Path

BASE = Path("docs/data/tennis")
SEASONS_DIR = BASE / "seasons"
OUTPUT = BASE / "history.json"

def normalise_match(m):
    """
    Force ALL matches into ONE structure
    (matches Sackmann format)
    """

    return {
        "tournament": m.get("tournament") or m.get("event") or m.get("tourney_name"),
        "surface": m.get("surface"),
        "round": m.get("round"),
        "date": m.get("date"),

        "winner": m.get("winner") or m.get("winner_name") or m.get("w_name"),
        "loser": m.get("loser") or m.get("loser_name") or m.get("l_name"),

        "score": m.get("score"),

        "best_of": m.get("best_of") or m.get("best_of_sets"),

        # optional fields (keep if exist)
        "winner_rank": m.get("winner_rank") or m.get("w_rank"),
        "loser_rank": m.get("loser_rank") or m.get("l_rank"),

        "winner_aces": m.get("winner_aces") or m.get("w_ace"),
        "loser_aces": m.get("loser_aces") or m.get("l_ace"),

        "winner_df": m.get("winner_df") or m.get("w_df"),
        "loser_df": m.get("loser_df") or m.get("l_df"),
    }


history = []

print("REBUILDING TENNIS HISTORY")

for file in sorted(SEASONS_DIR.glob("*.json")):
    print(f"Processing {file.name}")

    try:
        with open(file) as f:
            data = json.load(f)

        matches = data.get("matches") or data.get("games") or data

        for m in matches:
            fixed = normalise_match(m)

            # skip broken entries
            if not fixed["winner"] or not fixed["loser"]:
                continue

            history.append(fixed)

    except Exception as e:
        print(f"ERROR: {file} -> {e}")

# sort by date
history.sort(key=lambda x: x.get("date", ""))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT, "w") as f:
    json.dump({"matches": history}, f, indent=2)

print(f"DONE: {len(history)} matches saved")
