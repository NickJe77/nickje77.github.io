import json
from pathlib import Path

print("🏆 Building full Davis Cup structure")

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

def add_year(year, final, semis, qfs):
    # Final
    data.append({
        "year": year,
        "round": "Final",
        **final
    })

    # Semis
    for m in semis:
        data.append({
            "year": year,
            "round": "Semi Final",
            **m
        })

    # Quarter Finals
    for m in qfs:
        data.append({
            "year": year,
            "round": "Quarter Final",
            **m
        })

# -------------------------
# EXAMPLE FULL YEAR (2024)
# -------------------------

add_year(
    2024,
    final={"team1":"Italy","team2":"Netherlands","score":"2-0","winner":"Italy"},
    semis=[
        {"team1":"Italy","team2":"Serbia","score":"2-1","winner":"Italy"},
        {"team1":"Netherlands","team2":"Australia","score":"2-1","winner":"Netherlands"}
    ],
    qfs=[
        {"team1":"Italy","team2":"USA","score":"2-1","winner":"Italy"},
        {"team1":"Serbia","team2":"Great Britain","score":"2-1","winner":"Serbia"},
        {"team1":"Netherlands","team2":"Canada","score":"2-1","winner":"Netherlands"},
        {"team1":"Australia","team2":"Germany","score":"2-1","winner":"Australia"}
    ]
)

# -------------------------
# 2023
# -------------------------

add_year(
    2023,
    final={"team1":"Italy","team2":"Australia","score":"2-0","winner":"Italy"},
    semis=[
        {"team1":"Italy","team2":"Serbia","score":"2-1","winner":"Italy"},
        {"team1":"Australia","team2":"Finland","score":"2-0","winner":"Australia"}
    ],
    qfs=[
        {"team1":"Italy","team2":"Netherlands","score":"2-1","winner":"Italy"},
        {"team1":"Serbia","team2":"Great Britain","score":"2-0","winner":"Serbia"},
        {"team1":"Australia","team2":"Czech Republic","score":"2-1","winner":"Australia"},
        {"team1":"Finland","team2":"Canada","score":"2-1","winner":"Finland"}
    ]
)

# -------------------------
# SAVE
# -------------------------

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", len(data), "ties")
