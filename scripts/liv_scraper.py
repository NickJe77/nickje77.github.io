import requests
import json
from pathlib import Path

print("LIV SCRAPER (REAL API)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://api.livgolf.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}


def get_events():
    url = f"{BASE}/events"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("API FAILED")
        return []

    return r.json()


def build_data(events):
    output = []

    for e in events:
        try:
            output.append({
                "season": e.get("season"),
                "event": e.get("name"),
                "date": e.get("startDate"),
                "location": e.get("location", {}).get("name", ""),
                "winner": e.get("winner", {}).get("fullName", ""),
                "score": e.get("winningScore", "")
            })
        except:
            continue

    return output


events = get_events()

data = build_data(events)

with open(OUT / "all.json", "w") as f:
    json.dump(data, f, indent=2)

print("DONE")
