import requests
import json
from pathlib import Path

print("LIV SCRAPER (FLASHCORE JSON)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

# 🔥 Flashscore hidden endpoint
URL = "https://d.flashscore.com/x/feed/df_golf_6"

r = requests.get(URL, headers=HEADERS)

if r.status_code != 200:
    print("FAILED")
    exit()

data = r.text.split("\n")

events = []

for line in data:
    if "LIV" not in line:
        continue

    parts = line.split("|")

    try:
        event = {
            "event": parts[1],
            "date": parts[2],
            "winner": parts[3],
            "score": parts[4] if len(parts) > 4 else ""
        }

        events.append(event)
    except:
        continue

with open(OUT / "all.json", "w") as f:
    json.dump(events, f, indent=2)

print("DONE — DATA FOUND:", len(events))
