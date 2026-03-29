import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime

print("LIVE TENNIS SCRAPER (2025+)")

BASE = Path("docs/data/tennis")
MATCHES = BASE / "matches"
SEASONS = BASE / "seasons"

MATCHES.mkdir(parents=True, exist_ok=True)
SEASONS.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

YEARS = [2025, 2026]


def slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


def get_tournaments(year):
    url = f"https://www.tennisexplorer.com/results/?type=all&year={year}"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    links = []
    for a in soup.select("a"):
        href = a.get("href", "")
        if "/tournament/" in href:
            links.append("https://www.tennisexplorer.com" + href)

    return list(set(links))


def parse_match_row(row, tournament):
    cols = row.find_all("td")
    if len(cols) < 5:
        return None

    try:
        date = cols[0].text.strip()
        players = cols[2].text.strip().split(" - ")
        score = cols[3].text.strip()

        if len(players) != 2:
            return None

        p1, p2 = players

        return {
            "match_id": f"{date}_{slug(tournament)}_{slug(p1)}_{slug(p2)}",
            "date": date,
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
        }

    except:
        return None


def scrape_year(year):
    print(f"Scraping {year}")

    matches = []

    tournaments = get_tournaments(year)

    for t_url in tournaments[:200]:  # limit to avoid timeouts
        try:
            soup = BeautifulSoup(requests.get(t_url, headers=HEADERS).text, "html.parser")
            name = soup.title.text.split("|")[0].strip()

            rows = soup.select("table tr")

            for r in rows:
                m = parse_match_row(r, name)
                if m:
                    matches.append(m)

        except:
            continue

    return matches


for year in YEARS:
    data = scrape_year(year)

    (MATCHES / f"{year}.json").write_text(json.dumps(data, indent=2))
    (SEASONS / f"{year}.json").write_text(json.dumps(data, indent=2))

    print(f"{year}: {len(data)} matches saved")

print("DONE")
