import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time

print("TENNIS SCRAPER (CLEAN BUILD — 2025+)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
EVENT_DIR = BASE / "events"

MATCH_DIR.mkdir(parents=True, exist_ok=True)
EVENT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 2025
CURRENT_YEAR = datetime.utcnow().year


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
# GET TOURNAMENTS
# -------------------------
def get_tournaments(year):
    url = f"https://www.tennisexplorer.com/atp-men/{year}/"
    print(f"\nGetting tournaments for {year}")

    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.select("a"):
        href = a.get("href", "")

        if "/atp-men/" in href and "/results/" in href:
            full = "https://www.tennisexplorer.com" + href
            links.append(full)

    links = sorted(list(set(links)))

    print(f" → {len(links)} tournaments")
    return links


# -------------------------
# SCRAPE TOURNAMENT
# -------------------------
def scrape_tournament(url, year):
    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    name = url.split("/")[-3].replace("-", " ").title()

    matches = []

    rows = soup.find_all("tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 6:
            continue

        try:
            links = row.find_all("a")
            if len(links) < 2:
                continue

            player1 = links[0].text.strip()
            player2 = links[1].text.strip()

            round_val = cols[0].text.strip()
            score = cols[-1].text.strip()

            if not player1 or not player2:
                continue

            matches.append({
                "tournament": name,
                "surface": "Hard",
                "round": round_val,
                "player1": player1,
                "player2": player2,
                "score": score,
                "date": f"{year}0101",
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
    for year in range(START_YEAR, CURRENT_YEAR + 1):

        tournaments = get_tournaments(year)

        all_matches = []

        for t in tournaments:
            print("Scraping:", t)
            matches = scrape_tournament(t, year)
            all_matches.extend(matches)
            time.sleep(1)

        print(f"\n{year} MATCHES:", len(all_matches))

        if not all_matches:
            continue

        # SAVE MATCHES
        with open(MATCH_DIR / f"{year}.json", "w") as f:
            json.dump(all_matches, f, indent=2)

        # BUILD EVENTS
        events = build_events(all_matches, year)

        with open(EVENT_DIR / f"{year}.json", "w") as f:
            json.dump(events, f, indent=2)

        print(f"{year} EVENTS:", len(events))


run()
