import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🏆 Building FULL Davis Cup dataset (ITF legacy)")

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

# -------------------------
# YEARS TO BUILD
# -------------------------
START_YEAR = 1960   # you can push this back later
END_YEAR = 2024

# -------------------------
# BASE SEARCH URL
# -------------------------
BASE = "https://legacy.daviscup.com/en/results/tie/details.aspx?tieId="

# -------------------------
# THIS IS THE KEY IDEA:
# Tie IDs are numeric and roughly sequential
# -------------------------
START_ID = 1000
END_ID = 200000   # large range, script will filter valid ones

seen = set()

for tie_id in range(START_ID, END_ID):
    url = BASE + str(tie_id)

    try:
        r = requests.get(url, timeout=10)

        if "Davis Cup" not in r.text:
            continue

        soup = BeautifulSoup(r.text, "lxml")

        title = soup.find("title")
        if not title:
            continue

        text = title.get_text()

        # Example title:
        # "Italy v Netherlands | Davis Cup 2024 Final"
        if " v " not in text:
            continue

        parts = text.split("|")[0].strip()

        teams = parts.split(" v ")
        if len(teams) != 2:
            continue

        team1 = teams[0].strip()
        team2 = teams[1].strip()

        # extract year
        year_match = re.search(r"(19|20)\d{2}", text)
        if not year_match:
            continue

        year = int(year_match.group())

        if year < START_YEAR or year > END_YEAR:
            continue

        key = f"{year}-{team1}-{team2}"
        if key in seen:
            continue
        seen.add(key)

        # try to get result line
        score = ""

        body_text = soup.get_text(" ", strip=True)

        score_match = re.search(r"\d-\d", body_text)
        if score_match:
            score = score_match.group()

        data.append({
            "year": year,
            "round": "Unknown",
            "team1": team1,
            "team2": team2,
            "score": score,
            "winner": team1 if score.startswith("3") else team2 if score else ""
        })

        if len(data) % 100 == 0:
            print("Collected:", len(data))

    except:
        continue

print("Total ties collected:", len(data))

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", OUT)
