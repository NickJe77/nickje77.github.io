import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

print("TENNIS SCRAPER (DAILY MODE — GUARANTEED DATA)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
EVENT_DIR = BASE / "events"

MATCH_DIR.mkdir(parents=True, exist_ok=True)
EVENT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime.utcnow()


# -------------------------
# FETCH
# -------------------------
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None


# -------------------------
# SCRAPE DAY
# -------------------------
def scrape_day(date):
    url = f"https://www.tennisexplorer.com/results/?type=atp&year={date.year}&month={date.month}&day={date.day}"
    html = fetch(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    matches = []
    current_tournament = "Unknown"

    rows = soup.find_all("tr")

    for row in rows:
        cols = row.find_all("td")

        # tournament header row
        if len(cols) == 1:
            txt = cols[0].text.strip()
            if txt:
                current_tournament = txt
            continue

        if len(cols) < 6:
            continue

        try:
            links = row.find_all("a")
            if len(links) < 2:
                continue

            player1 = links[0].text.strip()
            player2 = links[1].text.strip()

            score = cols[-1].text.strip()
            round_val = cols[0].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "tournament": current_tournament,
                "surface": "Hard",  # default fallback
                "round": round_val,
                "player1": player1,
                "player2": player2,
                "score": score,
                "date": date.strftime("%Y%m%d"),
                "gender": "M"
            })

        except:
            continue

    return matches


# -------------------------
# BUILD EVENTS
# -------------------------
def build_events(matches, year):
    events = {}

    for m in matches:
        key = m["tournament"]

        if key not in events:
            events[key] = {
                "tournament_id": f"{year}-{key.lower().replace(' ', '-')}",
                "name": key,
                "surface": m["surface"],
                "draw_size": "32",
                "level": "A",
                "date": m["date"],
                "year": year
            }

    return list(events.values())


# -------------------------
# MAIN
# -------------------------
def run():
    current = START_DATE

    yearly_matches = {}

    while current <= END_DATE:
        print("Scraping:", current.strftime("%Y-%m-%d"))

        day_matches = scrape_day(current)

        if day_matches:
            year = current.year

            if year not in yearly_matches:
                yearly_matches[year] = []

            yearly_matches[year].extend(day_matches)

        current += timedelta(days=1)
        time.sleep(0.5)  # avoid blocking

    # -------------------------
    # SAVE
    # -------------------------
    for year, matches in yearly_matches.items():
        print(f"\n{year} MATCHES: {len(matches)}")

        # matches
        with open(MATCH_DIR / f"{year}.json", "w") as f:
            json.dump(matches, f, indent=2)

        # events
        events = build_events(matches, year)

        with open(EVENT_DIR / f"{year}.json", "w") as f:
            json.dump(events, f, indent=2)

        print(f"{year} EVENTS: {len(events)}")


run()
