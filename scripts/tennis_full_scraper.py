import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime

print("TENNIS SCRAPER (STABLE SOURCE)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
MATCH_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://www.tennisexplorer.com/matches/"

HEADERS = {"User-Agent": "Mozilla/5.0"}


def run():
    r = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tr")

    matches = []

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 6:
            continue

        try:
            player1 = cols[2].text.strip()
            player2 = cols[3].text.strip()
            score = cols[4].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "tournament": "Unknown",
                "surface": "Hard",
                "round": "R32",

                "player1": player1,
                "player2": player2,
                "score": score,

                "date": datetime.utcnow().strftime("%Y%m%d"),
                "gender": "M"
            })

        except:
            continue

    print(f"Saved {len(matches)} matches")

    with open(MATCH_DIR / "2026.json", "w") as f:
        json.dump(matches, f, indent=2)


run()
