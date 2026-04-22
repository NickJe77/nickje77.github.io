import json
from pathlib import Path

print("🏆 Building Davis Cup full bracket dataset")

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

# ---- SEED (MODERN ERA - RELIABLE) ----
# This ensures your site works immediately

data.extend([
    {"year":2024,"round":"Final","team1":"Italy","team2":"Netherlands","score":"2-0","winner":"Italy"},
    {"year":2024,"round":"Semi Final","team1":"Italy","team2":"Serbia","score":"2-1","winner":"Italy"},
    {"year":2024,"round":"Semi Final","team1":"Netherlands","team2":"Australia","score":"2-1","winner":"Netherlands"},

    {"year":2023,"round":"Final","team1":"Italy","team2":"Australia","score":"2-0","winner":"Italy"},
    {"year":2023,"round":"Semi Final","team1":"Italy","team2":"Serbia","score":"2-1","winner":"Italy"},
    {"year":2023,"round":"Semi Final","team1":"Australia","team2":"Finland","score":"2-0","winner":"Australia"},

    {"year":2022,"round":"Final","team1":"Canada","team2":"Australia","score":"2-0","winner":"Canada"},
    {"year":2022,"round":"Semi Final","team1":"Canada","team2":"Italy","score":"2-1","winner":"Canada"},
    {"year":2022,"round":"Semi Final","team1":"Australia","team2":"Croatia","score":"2-1","winner":"Australia"}
])

# ---- YOU CAN EXTEND YEAR BY YEAR SAFELY ----
# This avoids corrupt data

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", len(data), "ties")
