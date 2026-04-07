import requests
import json
from pathlib import Path

print("LIV FULL BUILDER")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

SEASONS = [2022, 2023, 2024]

BASE = "https://api.sportsdata.io/golf/v2/json/Tournaments"

API_KEY = "REPLACE_WITH_KEY"


def get_events(year):
    url = f"{BASE}/{year}"
    r = requests.get(url, params={"key": API_KEY})

    if r.status_code != 200:
        print("FAILED:", year)
        return []

    return r.json()


def build(events, year):
    output = []

    for e in events:
        if "LIV" not in e.get("Name", ""):
            continue

        output.append({
            "season": year,
            "event": e.get("Name"),
            "date": e.get("StartDate"),
            "location": e.get("City", ""),
            "winner": "",  # can extend with leaderboard endpoint
            "score": ""
        })

    return output


all_events = []

for year in SEASONS:
    print("Processing", year)

    events = get_events(year)
    data = build(events, year)

    with open(OUT / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    all_events.extend(data)

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("DONE")
