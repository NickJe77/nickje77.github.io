import json
from pathlib import Path

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path("docs/data/nrl/matches/2026")

games = [
{
"game_id":"2026R02G01",
"date":"2026-03-15",
"round":2,
"venue":"Suncorp Stadium",
"home_team":"Brisbane Broncos",
"away_team":"North Queensland Cowboys",
"home_score":24,
"away_score":18,
"players":[]
},
{
"game_id":"2026R02G02",
"date":"2026-03-15",
"round":2,
"venue":"Accor Stadium",
"home_team":"South Sydney Rabbitohs",
"away_team":"Sydney Roosters",
"home_score":12,
"away_score":28,
"players":[]
}
]

MATCH_DIR.mkdir(parents=True, exist_ok=True)

# load index
if INDEX.exists():
    with open(INDEX) as f:
        index = json.load(f)
else:
    index = {"season":2026,"games":[]}

for game in games:

    game_id = game["game_id"]

    match_file = MATCH_DIR / f"{game_id}.json"

    if not match_file.exists():

        with open(match_file,"w") as f:
            json.dump(game,f,indent=2)

        print(game_id,"created")

    if game_id not in index["games"]:
        index["games"].append(game_id)

index["games"] = sorted(index["games"])

with open(INDEX,"w") as f:
    json.dump(index,f,indent=2)

print("NRL update complete")
