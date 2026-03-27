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


def parse_score(row1_cols, row2_cols):
    score_parts = []

    for i in range(2, 7):  # columns 1–5 sets
        try:
            a = row1_cols[i].get_text(strip=True)
            b = row2_cols[i].get_text(strip=True)

            if a and b:
                score_parts.append(f"{a}-{b}")
        except:
            continue

    return " ".join(score_parts)


def parse_page(url, gender, year):
    print(f"Scraping {url}")

    soup = BeautifulSoup(get(url), "html.parser")

    rows = soup.select("table tr")

    matches = []

    i = 0
    while i < len(rows) - 1:
        r1 = rows[i]
        r2 = rows[i + 1]

        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        # must be valid pair
        if len(cols1) < 3 or len(cols2) < 3:
            i += 1
            continue

        links1 = r1.find_all("a")
        links2 = r2.find_all("a")

        if not links1 or not links2:
            i += 1
            continue

        p1 = links1[0].get_text(strip=True)
        p2 = links2[0].get_text(strip=True)

        # reject junk
        if not p1 or not p2:
            i += 1
            continue

        if p1 == p2:
            i += 1
            continue

        # date
        date = f"{year}0101"
        try:
            raw = cols1[0].get_text(strip=True)
            if "." in raw:
                d, m = raw.split(".")[:2]
                date = f"{year}{int(m):02d}{int(d):02d}"
        except:
            pass

        score = parse_score(cols1, cols2)

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

        i += 2  # move to next match pair

    print(f"✔ {len(matches)} matches parsed")
    return matches


def save(year, matches):
    path = BASE / f"{year}.json"
    path.write_text(json.dumps(matches, indent=2))
    print(f"Saved {path}")


def main():
    print("RUNNING TENNIS SCRAPER (PAIR-ROW FIX)")

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
