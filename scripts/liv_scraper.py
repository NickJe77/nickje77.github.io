import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup

print("LIV SCRAPER (RESULTS TABLE VERSION)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://en.wikipedia.org/wiki/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


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


def scrape_event(slug, year):
    url = BASE + slug
    print("Fetching:", url)

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("FAILED:", slug)
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # event name
    title = soup.find("h1")
    event_name = title.text.strip() if title else slug

    # date/location (still safe from infobox)
    date = ""
    location = ""

    infobox = soup.find("table", {"class": "infobox"})
    if infobox:
        for row in infobox.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue

            label = th.text.lower()
            val = td.text.strip()

            if "date" in label:
                date = val
            if "location" in label:
                location = val

    # 🔥 FIND RESULTS TABLE
    winner = ""
    score = ""

    tables = soup.find_all("table")

    for table in tables:
        text = table.get_text(" ", strip=True).lower()

        # look for leaderboard style table
        if "pos" in text and "player" in text and "score" in text:

            rows = table.find_all("tr")

            for row in rows:
                cols = [td.text.strip() for td in row.find_all("td")]

                if len(cols) < 3:
                    continue

                # winner is first row (position 1)
                if cols[0] == "1" or cols[0] == "T1":
                    winner = cols[1]
                    score = cols[-1]
                    break

            if winner:
                break

    return {
        "season": year,
        "event": event_name,
        "date": date,
        "location": location,
        "winner": winner,
        "score": score
    }


# -----------------------
# RUN
# -----------------------

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
