import json
from pathlib import Path

print("🏆 Fixing Davis Cup dataset (adding doubles)")

IN = Path("docs/data/tennis/davis_cup/2025.json")  # your current file
OUT = Path("docs/data/tennis/davis_cup/2025_fixed.json")

with open(IN) as f:
    matches = json.load(f)

fixed = []
current_tie = []

def flush_tie(tie):
    if not tie:
        return

    # if only 4 matches → doubles missing
    if len(tie) == 4:
        tie.insert(2, {
            "player1": "Unknown / Unknown",
            "player2": "Unknown / Unknown",
            "score": "",
            "match_type": "Doubles"
        })

    fixed.extend(tie)

for m in matches:
    current_tie.append(m)

    # detect end of tie (5 matches max)
    if len(current_tie) == 5:
        flush_tie(current_tie)
        current_tie = []

# flush leftover
flush_tie(current_tie)

with open(OUT, "w") as f:
    json.dump(fixed, f, indent=2)

print("✅ Done. Matches:", len(fixed))
