import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime

print("NRL BASE BUILDER")

SEASON = 2026
URL = "https://www.nrl.com/draw/"

OUTPUT = Path(f"docs/data/nrl/seasons/{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch():
    r = requests.get(URL, headers=HEADERS)
    return r.text


def parse(html):

    soup = BeautifulSoup(html, "html.parser")

    games = []

    matches = soup.select("a[href*='/draw/']")

    for m in matches:

        text = m.get_text(" ", strip=True)

        if "Round" not in text:
            continue

        try:
            parts = text.split()

            # crude but stable parsing
            home = parts[parts.index("vs") - 1]
            away = parts[parts.index("vs") + 1]

            games.append({
                "season": SEASON,
                "home_team": home,
                "away_team": away
            })

        except:
            continue

    return games


def main():

    html = fetch()
    games = parse(html)

    OUTPUT.write_text(json.dumps(games, indent=2))

    print("Saved", len(games), "games")


if __name__ == "__main__":
    main()
