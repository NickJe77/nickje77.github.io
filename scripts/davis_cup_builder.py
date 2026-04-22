import json
from pathlib import Path

print("🏆 Building Davis Cup dataset (guaranteed data)")

# Manually structured matches (reliable seed)
# You can expand this later

matches = [
    {
        "player1": "Player A",
        "player2": "Player B",
        "score": "6-4 6-4",
        "match_type": "Singles"
    },
    {
        "player1": "Player C / Player D",
        "player2": "Player E / Player F",
        "score": "6-3 3-6 7-6",
        "match_type": "Doubles"
    }
]

OUT = Path("docs/data/tennis/davis_cup/2025.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", len(matches))
