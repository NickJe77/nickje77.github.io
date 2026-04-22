import json
from pathlib import Path

print("🏆 Building Davis Cup dataset (test with real structure)")

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

# ---- HARD TEST DATA (KNOWN CORRECT STRUCTURE) ----
for year in range(2000, 2025):
    data.append({
        "year": year,
        "round": "Final",
        "team1": "Team A",
        "team2": "Team B",
        "score": "3-2",
        "winner": "Team A"
    })

print("Total ties:", len(data))

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", OUT)
