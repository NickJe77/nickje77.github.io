import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup

print("LIV SCRAPER (EVENT-LEVEL — REAL DATA)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://en.wikipedia.org/wiki/"

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------------
# EVENT LIST (THIS PART IS STABLE)
# -----------------------------------

EVENTS = {
    2022: [
        "2022_LIV_Golf_Invitational_London",
        "2022_LIV_Golf_Invitational_Portland",
        "2022_LIV_Golf_Invitational_Bedminster",
        "2022_LIV_Golf_Invitational_Boston",
        "2022_LIV_Golf_Invitational_Chicago",
        "2022_LIV_Golf_Invitational_Bangkok",
        "2022_LIV_Golf_Invitational_Jeddah",
        "2022_LIV_Golf_Invitational_Miami",
    ],
    2023: [
        "2023_LIV_Golf_Mayakoba",
        "2023_LIV_Golf_Tucson",
        "2023_LIV_Golf_Orlando",
        "2023_LIV_Golf_Adelaide",
        "2023_LIV_Golf_Singapore",
        "2023_LIV_Golf_Tulsa",
        "2023_LIV_Golf_DC",
        "2023_LIV_Golf_Andalucia",
        "2023_LIV_Golf_London",
        "2023_LIV_Golf_Greenbrier",
        "2023_LIV_Golf_Bedminster",
        "2023_LIV_Golf_Chicago",
        "2023_LIV_Golf_Jeddah",
        "2023_LIV_Golf_Miami",
    ]
}


# -----------------------------------
# SCRAPE EVENT PAGE
# -----------------------------------

def scrape_event(slug, year):
    url = BASE + slug
    print("Fetching:", url)

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("h1")
    event_name = title.text.strip() if title else slug

    infobox = soup.find("table", {"class": "infobox"})

    date = ""
    location = ""
    winner = ""
    score = ""

    if infobox:
        rows = infobox.find_all("tr")

        for row in rows:
            th = row.find("th")
            td = row.find("td")

            if not th or not td:
                continue

            label = th.text.strip().lower()
            value = td.text.strip()

            if "date" in label:
                date = value
            elif "location" in label:
                location = value
            elif "winner" in label:
                winner = value
            elif "score" in label:
                score = value

    return {
        "season": year,
        "event": event_name,
        "date": date,
        "location": location,
        "winner": winner,
        "score": score
    }


# -----------------------------------
# RUN
# -----------------------------------

all_events = []

for year, slugs in EVENTS.items():
    season_events = []

    for slug in slugs:
        data = scrape_event(slug, year)

        if data:
            season_events.append(data)

    with open(OUT / f"{year}.json", "w") as f:
        json.dump(season_events, f, indent=2)

    all_events.extend(season_events)

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE — REAL DATA BUILT")
