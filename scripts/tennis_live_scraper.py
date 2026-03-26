import requests
from bs4 import BeautifulSoup
import json
import os
import time

OUTPUT_DIR = "docs/data/tennis/matches"

BASE = "https://r.jina.ai/http://www.tennisabstract.com/cgi-bin/tourneys.cgi?year="


def get_soup(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except:
        return None
    return None


def get_tournaments(year):
    soup = get_soup(BASE + str(year))
    tournaments = []

    if not soup:
        return tournaments

    for a in soup.find_all("a"):
        href = a.get("href","")
        if "tourney.cgi?t=" in href:
            tid = href.split("t=")[-1]
            name = a.text.strip()
            tournaments.append((tid,name))

    return tournaments


def get_matches(tid):
    url = f"https://r.jina.ai/http://www.tennisabstract.com/cgi-bin/tourney.cgi?t={tid}"
    soup = get_soup(url)

    matches = []

    if not soup:
        return matches

    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        try:
            matches.append({
                "round": cols[0].text.strip(),
                "player1": cols[1].text.strip(),
                "player2": cols[2].text.strip(),
                "score": cols[3].text.strip()
            })
        except:
            continue

    return matches


def update_year(year):

    print(f"\nYEAR {year}")

    tournaments = get_tournaments(year)
    print(f"Found {len(tournaments)} tournaments")

    all_matches = []

    for tid,name in tournaments:

        print(" ",name)

        matches = get_matches(tid)

        for m in matches:
            m["tournament"] = name
            m["year"] = year
            m["gender"] = "M"  # default (can expand later)

        all_matches += matches

        time.sleep(1)

    path = f"{OUTPUT_DIR}/{year}.json"

    if os.path.exists(path):
        existing = json.load(open(path))
    else:
        existing = []

    existing += all_matches

    json.dump(existing, open(path,"w"), indent=2)

    print(f"{year} updated ({len(existing)})")


def main():
    for year in [2025, 2026]:
        update_year(year)


if __name__ == "__main__":
    main()
