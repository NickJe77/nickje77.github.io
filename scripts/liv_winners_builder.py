import json
from pathlib import Path

print("LIV BUILDER (FULL DATA + FUTURE READY)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

# ---------------------------
# DATA
# ---------------------------
data = [

    # 2022
    {"year": 2022, "event": "LIV Golf London", "winner": "Charl Schwartzel"},
    {"year": 2022, "event": "LIV Golf Portland", "winner": "Branden Grace"},
    {"year": 2022, "event": "LIV Golf Bedminster", "winner": "Henrik Stenson"},
    {"year": 2022, "event": "LIV Golf Boston", "winner": "Dustin Johnson"},
    {"year": 2022, "event": "LIV Golf Chicago", "winner": "Cameron Smith"},
    {"year": 2022, "event": "LIV Golf Bangkok", "winner": "Eugenio Chacarra"},
    {"year": 2022, "event": "LIV Golf Jeddah", "winner": "Brooks Koepka"},
    {"year": 2022, "event": "LIV Golf Miami", "winner": "Dustin Johnson"},

    # 2023
    {"year": 2023, "event": "LIV Golf Mayakoba", "winner": "Charles Howell III"},
    {"year": 2023, "event": "LIV Golf Tucson", "winner": "Danny Lee"},
    {"year": 2023, "event": "LIV Golf Orlando", "winner": "Brooks Koepka"},
    {"year": 2023, "event": "LIV Golf Adelaide", "winner": "Talor Gooch"},
    {"year": 2023, "event": "LIV Golf Singapore", "winner": "Talor Gooch"},
    {"year": 2023, "event": "LIV Golf Tulsa", "winner": "Dustin Johnson"},
    {"year": 2023, "event": "LIV Golf DC", "winner": "Harold Varner III"},
    {"year": 2023, "event": "LIV Golf Andalucia", "winner": "Talor Gooch"},
    {"year": 2023, "event": "LIV Golf London", "winner": "Cameron Smith"},
    {"year": 2023, "event": "LIV Golf Greenbrier", "winner": "Bryson DeChambeau"},
    {"year": 2023, "event": "LIV Golf Bedminster", "winner": "Cameron Smith"},
    {"year": 2023, "event": "LIV Golf Chicago", "winner": "Talor Gooch"},
    {"year": 2023, "event": "LIV Golf Jeddah", "winner": "Brooks Koepka"},
    {"year": 2023, "event": "LIV Golf Miami", "winner": "Talor Gooch"},

    # 2024 (example structure)
    {"year": 2024, "event": "LIV Golf Mayakoba", "winner": "Joaquin Niemann"},
    {"year": 2024, "event": "LIV Golf Las Vegas", "winner": "Dustin Johnson"},

    # 2025 (PLACEHOLDER - YOU UPDATE WEEKLY)
    {"year": 2025, "event": "LIV Golf Adelaide", "winner": ""},
    {"year": 2025, "event": "LIV Golf Singapore", "winner": ""},

    # 2026 (LIVE BUILD YEAR)
    {"year": 2026, "event": "LIV Golf Adelaide", "winner": ""},
    {"year": 2026, "event": "LIV Golf Singapore", "winner": ""},
]

# ---------------------------
# BUILD JSON
# ---------------------------
rows = []

for r in data:
    rows.append({
        "tour": "liv",
        "year": r["year"],
        "date": "",
        "event": r["event"],
        "winner": r["winner"],
        "score": "",
        "venue": "",
        "country": "",
        "url": ""
    })

rows.sort(key=lambda x: (x["year"], x["event"]), reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(rows, f, indent=2)

print("DONE:", len(rows))
