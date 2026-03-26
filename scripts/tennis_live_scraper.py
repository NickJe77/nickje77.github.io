import requests
from bs4 import BeautifulSoup
import json
import os
import time

OUTPUT_DIR = "docs/data/tennis/matches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except:
        return None
    return None


# ---------------------------------
# ATP CURRENT TOURNAMENTS
# ---------------------------------
def get_atp_tournaments():
    soup = get_soup("https://www.atptour.com/en/scores/current")
    tournaments = []

    if not soup:
        return tournaments

    for a in soup.select("a"):
        href = a.get("href","")
        if "/scores/current/" in href and href.endswith("/results"):
            tournaments.append("https://www.atptour.com" + href)

    return list(set(tournaments))


# ---------------------------------
# PARSE MATCHES
# ---------------------------------
def parse_matches(url, gender):

    soup = get_soup(url)
    matches = []

    if not soup:
        return matches

    for row in soup.select(".day-table tr"):

        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        try:
            p1 = cols[0].get_text(strip=True)
            p2 = cols[1].get_text(strip=True)
            score = cols[2].get_text(strip=True)

            matches.append({
                "player1": p1,
                "player2": p2,
                "score": score,
                "gender": gender
            })
        except:
            continue

    return matches


# ---------------------------------
# UPDATE YEAR
# ---------------------------------
def update_year(year):

    print(f"\nUpdating {year}")

    matches = []

    # ATP
    for t in get_atp_tournaments():
        print("ATP:", t)

        m = parse_matches(t, "M")

        for x in m:
            x["tournament"] = t.split("/")[-2]
            x["year"] = year

        matches += m
        time.sleep(1)

    # TODO: add WTA same way

    path = f"{OUTPUT_DIR}/{year}.json"

    if os.path.exists(path):
        existing = json.load(open(path))
    else:
        existing = []

    existing += matches

    json.dump(existing, open(path,"w"), indent=2)

    print(f"{year} updated: {len(existing)} matches")


def main():
    update_year(2025)
    update_year(2026)


if __name__ == "__main__":
    main()
