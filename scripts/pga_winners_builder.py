import requests
import json
from pathlib import Path
import time

print("PGA WINNERS BUILDER (SAFE FIX)")

OUTPUT = Path("docs/data/golf")
OUTPUT.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUTPUT / "pga_winners.json"

BASE = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_PAGES = 5

all_rows = []


def get_page(page):
    url = f"{BASE}?limit=50&dates=2026&page={page}"
    r = requests.get(url, headers=HEADERS, timeout=10)

    if r.status_code != 200:
        return []

    return r.json().get("events", [])


def extract_winner(event):
    try:
        comp = event["competitions"][0]
        players = comp["competitors"]

        winner = sorted(players, key=lambda x: int(x.get("score", 9999)))[0]

        return winner["athlete"]["displayName"], winner.get("score", "")
    except:
        return None, None


for page in range(1, MAX_PAGES + 1):
    print(f"PAGE {page}")

    events = get_page(page)

    if not events:
        break

    for e in events:
        try:
            name = e.get("name")
            date = e.get("date", "")[:10]

            winner, score = extract_winner(e)

            if not winner:
                continue

            comp = e["competitions"][0]

            row = {
                "tour": "pga",
                "year": int(date[:4]) if date else "",
                "date": date,
                "event": name,
                "winner": winner,
                "score": score,
                "venue": comp.get("venue", {}).get("fullName", ""),
                "country": comp.get("venue", {}).get("address", {}).get("country", ""),
                "url": ""
            }

            all_rows.append(row)

        except:
            continue

    time.sleep(1)


# remove duplicates
seen = set()
unique = []
for r in all_rows:
    key = (r["event"], r["date"])
    if key not in seen:
        seen.add(key)
        unique.append(r)

unique.sort(key=lambda x: x["date"], reverse=True)

with open(OUT_FILE, "w") as f:
    json.dump(unique, f, indent=2)

print("DONE:", len(unique))
