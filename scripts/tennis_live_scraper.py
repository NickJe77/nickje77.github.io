import json
import time
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = Path("docs/data/tennis/seasons")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.utcnow().year
YEARS = [2025, CURRENT_YEAR]

URLS = {
    "M": lambda y: f"https://www.tennisexplorer.com/results/?type=ATP&year={y}",
    "F": lambda y: f"https://www.tennisexplorer.com/results/?type=WTA&year={y}",
}


def get(url):
    return SESSION.get(url, timeout=30).text


def is_score(text):
    return any(c.isdigit() for c in text) and "-" in text


def parse_page(url, gender, year):
    print(f"Scraping {url}")

    soup = BeautifulSoup(get(url), "html.parser")

    matches = []
    rows = soup.select("tr")

    for tr in rows:
        links = tr.find_all("a")

        # must have at least 2 player links
        if len(links) < 2:
            continue

        p1 = links[0].get_text(strip=True)
        p2 = links[1].get_text(strip=True)

        # reject junk
        if not p1 or not p2:
            continue
        if p1 == p2:
            continue
        if len(p2) < 3:
            continue

        cells = [td.get_text(strip=True) for td in tr.find_all("td")]

        # find score anywhere in row
        score = ""
        for c in cells:
            if is_score(c):
                score = c
                break

        if not score:
            continue

        # find date
        date = f"{year}0101"
        if cells:
            raw = cells[0]
            if "." in raw:
                try:
                    d, m = raw.split(".")[:2]
                    date = f"{year}{int(m):02d}{int(d):02d}"
                except:
                    pass

        matches.append({
            "tournament": "",
            "surface": "",
            "round": "",
            "player1": p1,
            "player2": p2,
            "score": score,
            "date": date,
            "gender": gender,
        })

    print(f"✔ {len(matches)} matches parsed")
    return matches


def save(year, matches):
    path = BASE / f"{year}.json"
    path.write_text(json.dumps(matches, indent=2))
    print(f"Saved {path}")


def main():
    print("RUNNING TENNIS SCRAPER (FIXED)")

    for year in YEARS:
        year_matches = []

        for gender in ["M", "F"]:
            try:
                url = URLS[gender](year)
                data = parse_page(url, gender, year)
                year_matches.extend(data)
                time.sleep(2)
            except Exception as e:
                print(f"FAIL {year} {gender}: {e}")

        save(year, year_matches)

    print("DONE")


if __name__ == "__main__":
    main()
