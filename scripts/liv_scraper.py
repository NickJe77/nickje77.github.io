import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV SCRAPER (FLASHSCORE)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# LIV competitions on Flashscore
URL = "https://www.flashscore.com/golf/liv-golf/"

r = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(r.text, "html.parser")

events = []

# find all tournament links
links = soup.find_all("a", {"class": "event__name"})

for link in links:
    event_name = link.text.strip()
    href = link.get("href")

    if not href:
        continue

    event_url = "https://www.flashscore.com" + href + "results/"

    print("Fetching:", event_name)

    res = requests.get(event_url, headers=HEADERS)
    s = BeautifulSoup(res.text, "html.parser")

    rows = s.find_all("div", {"class": "event__match"})

    for row in rows:
        player = row.find("div", {"class": "event__participant"})
        score = row.find("div", {"class": "event__score"})

        if not player:
            continue

        winner = player.text.strip()
        score_val = score.text.strip() if score else ""

        events.append({
            "event": event_name,
            "winner": winner,
            "score": score_val
        })

# save
with open(OUT / "all.json", "w") as f:
    json.dump(events, f, indent=2)

print("DONE")
