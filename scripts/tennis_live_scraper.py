import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime, timedelta

print("TENNIS SCRAPER (FINAL WORKING VERSION)")

BASE = Path("docs/data/tennis")
MATCHES = BASE / "matches"
SEASONS = BASE / "seasons"

MATCHES.mkdir(parents=True, exist_ok=True)
SEASONS.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

YEARS = [2025, 2026]


def slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


def get_dates(year):
    start = datetime(year, 1, 1)
    end = datetime.utcnow()
    for i in range((end - start).days + 1):
        yield start + timedelta(days=i)


def scrape_day(date):
    url = f"https://www.tennisexplorer.com/matches/?year={date.year}&month={date.month}&day={date.day}"

    r = session.get(url)

    if "result" not in r.text:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    matches = []

    tables = soup.select("table.result")

    for table in tables:
        header = table.find_previous("tr", class_="head")
        tournament = header.text.strip() if header else "Unknown"

        for row in table.select("tr"):
            cols = row.find_all("td")

            if len(cols) < 4:
                continue

            try:
                players = cols[2].text.strip().split("-")
                score = cols[3].text.strip()

                if len(players) != 2:
                    continue

                p1 = players[0].strip()
                p2 = players[1].strip()

                matches.append({
                    "match_id": f"{date.date()}_{slug(p1)}_{slug(p2)}",
                    "date": str(date.date()),
                    "tournament": tournament,
                    "surface": "",
                    "round": "",
                    "player1": p1,
                    "player2": p2,
                    "winner": p1,
                    "loser": p2,
                    "score": score,
                    "gender": "",
                    "best_of": 3,
                    "draw_size": 0,
                    "minutes": 0,
                    "tourney_level": "",
                    "tourney_id": ""
                })

            except:
                continue

    return matches


for year in YEARS:
    print(f"Processing {year}")

    all_matches = []

    for d in get_dates(year):
        daily = scrape_day(d)
        all_matches.extend(daily)

    print(f"{year}: {len(all_matches)} matches")

    (MATCHES / f"{year}.json").write_text(json.dumps(all_matches, indent=2))
    (SEASONS / f"{year}.json").write_text(json.dumps(all_matches, indent=2))

print("DONE")
