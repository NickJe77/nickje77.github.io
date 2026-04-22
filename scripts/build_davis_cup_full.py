import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏆 Building Davis Cup FULL dataset")

START_YEAR = 2000
END_YEAR = 2024

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

for year in range(START_YEAR, END_YEAR + 1):
    url = f"https://en.wikipedia.org/wiki/{year}_Davis_Cup"
    print("→", url)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")

    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            if len(cols) < 3:
                continue

            team1 = cols[0]
            team2 = cols[1]
            score = cols[2]

            if "-" not in score:
                continue

            data.append({
                "year": year,
                "round": "Unknown",
                "team1": team1,
                "team2": team2,
                "score": score,
                "winner": team1 if score.startswith("3") else team2
            })

print("Total ties:", len(data))

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", OUT)
