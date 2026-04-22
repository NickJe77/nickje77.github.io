import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🏆 Building Davis Cup FULL dataset")

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
}

BASE = "https://legacy.daviscup.com/en/results/tie/details.aspx?tieId="

START_ID = 1
END_ID = 20000   # keep this SMALL first to prove it works

for tie_id in range(START_ID, END_ID):
    url = BASE + str(tie_id)

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            continue

        soup = BeautifulSoup(r.text, "lxml")

        title = soup.find("title")
        if not title:
            continue

        text = title.get_text()

        if " v " not in text:
            continue

        teams_part = text.split("|")[0].strip()
        teams = teams_part.split(" v ")

        if len(teams) != 2:
            continue

        team1 = teams[0].strip()
        team2 = teams[1].strip()

        year_match = re.search(r"(19|20)\d{2}", text)
        if not year_match:
            continue

        year = int(year_match.group())

        # extract score from page text
        body = soup.get_text(" ", strip=True)
        score_match = re.search(r"\d-\d", body)
        score = score_match.group() if score_match else ""

        data.append({
            "year": year,
            "round": "Unknown",
            "team1": team1,
            "team2": team2,
            "score": score,
            "winner": team1 if score.startswith("3") else team2 if score else ""
        })

        if len(data) % 50 == 0:
            print("Collected:", len(data))

    except:
        continue

print("Total ties:", len(data))

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", OUT)
