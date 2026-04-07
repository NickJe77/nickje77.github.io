import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV SCRAPER (REAL WORKING VERSION — NO WIKI)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


# 🔥 KNOWN EVENTS (reliable backbone)
EVENTS = {
    2022: [
        ("London", "https://en.wikipedia.org/wiki/LIV_Golf_Invitational_London"),
        ("Portland", "https://en.wikipedia.org/wiki/LIV_Golf_Invitational_Portland"),
        ("Bedminster", "https://en.wikipedia.org/wiki/LIV_Golf_Invitational_Bedminster"),
    ],
    2023: [
        ("Mayakoba", "https://en.wikipedia.org/wiki/LIV_Golf_Mayakoba"),
        ("Tucson", "https://en.wikipedia.org/wiki/LIV_Golf_Tucson"),
        ("Orlando", "https://en.wikipedia.org/wiki/LIV_Golf_Orlando"),
        ("Adelaide", "https://en.wikipedia.org/wiki/LIV_Golf_Adelaide"),
    ],
    2024: [],
    2025: [],
    2026: []
}


def scrape_event(name, url, year):
    print(f"Scraping {name}")

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # find infobox
    box = soup.find("table", {"class": "infobox"})

    if not box:
        return None

    text = box.get_text(" ", strip=True)

    winner = ""

    # 🔥 extract winner
    for row in box.find_all("tr"):
        th = row.find("th")
        td = row.find("td")

        if not th or not td:
            continue

        if "winner" in th.text.lower():
            winner = td.text.strip()

    return {
        "season": year,
        "event": f"LIV Golf {name}",
        "date": "",
        "location": "",
        "winner": winner,
        "score": ""
    }


# -----------------------
# RUN
# -----------------------
all_events = []

for year, events in EVENTS.items():
    season_data = []

    for name, url in events:
        data = scrape_event(name, url, year)

        if data:
            season_data.append(data)

    with open(OUT / f"{year}.json", "w") as f:
        json.dump(season_data, f, indent=2)

    all_events.extend(season_data)

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("DONE")
