import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("IPL 2026 FINAL SCRAPER")

URL = "https://www.espncricinfo.com/series/ipl-2026-1510719/match-results"

OUTPUT = Path("docs/data/ipl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
    "Connection": "keep-alive"
})

# 🔁 retry logic
for i in range(3):
    r = session.get(URL)
    if r.status_code == 200 and len(r.text) > 5000:
        break
    print("Retrying...", i)

print("STATUS:", r.status_code)
print("LEN:", len(r.text))

soup = BeautifulSoup(r.text, "html.parser")

matches = []

cards = soup.select("a[href*='/match/']")

for a in cards:
    text = a.get_text(" ", strip=True)

    if " vs " not in text:
        continue

    try:
        team1, rest = text.split(" vs ")
        team2 = rest.split(",")[0]

        match = {
            "teams": [team1.strip(), team2.strip()],
            "text": text,
            "link": "https://www.espncricinfo.com" + a["href"]
        }

        matches.append(match)

    except:
        continue

# remove duplicates
unique = {m["link"]: m for m in matches}.values()

with open(OUTPUT, "w") as f:
    json.dump({
        "season": "2026",
        "matches": list(unique)
    }, f, indent=2)

print("DONE:", len(unique))
