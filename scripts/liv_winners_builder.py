import json
from pathlib import Path

print("LIV BUILDER (FULL CLEAN DATASET)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "liv_winners.json"

data = [

    # -----------------
    # 2022 (FULL)
    # -----------------
    {"year": 2022, "event": "LIV Golf London", "winner": "Charl Schwartzel"},
    {"year": 2022, "event": "LIV Golf Portland", "winner": "Branden Grace"},
    {"year": 2022, "event": "LIV Golf Bedminster", "winner": "Henrik Stenson"},
    {"year": 2022, "event": "LIV Golf Boston", "winner": "Dustin Johnson"},
    {"year": 2022, "event": "LIV Golf Chicago", "winner": "Cameron Smith"},
    {"year": 2022, "event": "LIV Golf Bangkok", "winner": "Eugenio Chacarra"},
    {"year": 2022, "event": "LIV Golf Jeddah", "winner": "Brooks Koepka"},
    {"year": 2022, "event": "LIV Golf Miami (Team Championship)", "winner": "Dustin Johnson"},

    # -----------------
    # 2023 (FULL)
    # -----------------
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
    {"year": 2023, "event": "LIV Golf Miami (Team Championship)", "winner": "Talor Gooch"},

    # -----------------
    # 2024 (KNOWN RESULTS)
    # -----------------
    {"year": 2024, "event": "LIV Golf Mayakoba", "winner": "Joaquin Niemann"},
    {"year": 2024, "event": "LIV Golf Las Vegas", "winner": "Dustin Johnson"},
    {"year": 2024, "event": "LIV Golf Jeddah", "winner": "Joaquin Niemann"},
    {"year": 2024, "event": "LIV Golf Hong Kong", "winner": "Abraham Ancer"},
    {"year": 2024, "event": "LIV Golf Miami", "winner": "Dean Burmester"},
    {"year": 2024, "event": "LIV Golf Adelaide", "winner": "Brendan Steele"},

    # -----------------
    # 2025 (LIVE YEAR → WILL FILL)
    # -----------------
    {"year": 2025, "event": "LIV Golf Adelaide", "winner": ""},
    {"year": 2025, "event": "LIV Golf Singapore", "winner": ""},

    # -----------------
    # 2026 (CURRENT YEAR)
    # -----------------
    {"year": 2026, "event": "LIV Golf Adelaide", "winner": ""},
    {"year": 2026, "event": "LIV Golf Singapore", "winner": ""},
]

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
