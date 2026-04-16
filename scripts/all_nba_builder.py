import json
from pathlib import Path

print("ALL-NBA BUILDER (STATIC — WORKING)")

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

data = [
  {
    "season": "2024-25",
    "first_team": [
      {"player":"Giannis Antetokounmpo","team":"MIL"},
      {"player":"Shai Gilgeous-Alexander","team":"OKC"},
      {"player":"Nikola Jokic","team":"DEN"},
      {"player":"Donovan Mitchell","team":"CLE"},
      {"player":"Jayson Tatum","team":"BOS"}
    ],
    "second_team": [
      {"player":"Jalen Brunson","team":"NYK"},
      {"player":"Stephen Curry","team":"GSW"},
      {"player":"Anthony Edwards","team":"MIN"},
      {"player":"LeBron James","team":"LAL"},
      {"player":"Evan Mobley","team":"CLE"}
    ],
    "third_team": [
      {"player":"Cade Cunningham","team":"DET"},
      {"player":"Tyrese Haliburton","team":"IND"},
      {"player":"James Harden","team":"LAC"},
      {"player":"Karl-Anthony Towns","team":"NYK"},
      {"player":"Jalen Williams","team":"OKC"}
    ]
  },
  {
    "season": "2023-24",
    "first_team": [
      {"player":"Giannis Antetokounmpo","team":"MIL"},
      {"player":"Luka Doncic","team":"DAL"},
      {"player":"Shai Gilgeous-Alexander","team":"OKC"},
      {"player":"Nikola Jokic","team":"DEN"},
      {"player":"Jayson Tatum","team":"BOS"}
    ],
    "second_team": [
      {"player":"Jalen Brunson","team":"NYK"},
      {"player":"Anthony Davis","team":"LAL"},
      {"player":"Kevin Durant","team":"PHX"},
      {"player":"Anthony Edwards","team":"MIN"},
      {"player":"Kawhi Leonard","team":"LAC"}
    ],
    "third_team": []
  }
]

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
