import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("IPL 2026 RESULTS SCRAPER (WORKING)")

URL = "https://www.espncricinfo.com/series/ipl-2026-1510719/match-results"

OUTPUT = Path("docs/data/ipl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=headers)

if r.status_code != 200:
    print("FAILED:", r.status_code)
    exit()

soup = BeautifulSoup(r.text, "html.parser")

matches = []

cards = soup.find_all("a", href=True)

for a in cards:
    href = a["href"]

    if "/match/" not in href:
        continue

    text = a.get_text(" ", strip=True)

    if "v" not in text and "vs" not in text:
        continue

    try:
        parts = text.split("vs")
        if len(parts) < 2:
            parts = text.split("v")

        team1 = parts[0].strip()
        rest = parts[1].strip()

        team2 = rest.split(",")[0].strip()

        match = {
            "teams": [team1, team2],
            "text": text,
            "link": "https://www.espncricinfo.com" + href
        }

        matches.append(match)

    except:
        continue

# remove duplicates
unique = []
seen = set()

for m in matches:
    key = m["link"]
    if key not in seen:
        unique.append(m)
        seen.add(key)

out = {
    "season": "2026",
    "matches": unique
}

with open(OUTPUT, "w") as f:
    json.dump(out, f, indent=2)

print("DONE:", len(unique), "matches")
