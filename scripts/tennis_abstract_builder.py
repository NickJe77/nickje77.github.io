import os
import json
import time
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = "docs/data/tennis/matches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_YEAR_URL = "https://www.tennisabstract.com/cgi-bin/tourneys.cgi?year="
BASE_TOURNEY_URL = "https://www.tennisabstract.com/cgi-bin/tourney.cgi?t="

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
})


# -----------------------------
# SAFE GET WITH RETRIES
# -----------------------------
def get_soup(url):
    for i in range(3):
        try:
            r = session.get(url, timeout=20)

            if r.status_code == 200 and len(r.text) > 500:
                return BeautifulSoup(r.text, "html.parser")

            time.sleep(2)
        except:
            time.sleep(2)

    print("FAIL:", url)
    return None


# -----------------------------
# GET TOURNAMENTS (FIXED PARSE)
# -----------------------------
def get_tournaments(year):
    url = BASE_YEAR_URL + str(year)
    soup = get_soup(url)

    tournaments = []

    if not soup:
        return tournaments

    # 🔥 FIX: Only grab valid tournament links
    for a in soup.find_all("a"):
        href = a.get("href", "")

        if "tourney.cgi?t=" in href:
            tid = href.split("t=")[-1].strip()
            name = a.text.strip()

            if name and len(name) < 50:
                tournaments.append({
                    "id": tid,
                    "name": name
                })

    return tournaments


# -----------------------------
# PARSE MATCHES
# -----------------------------
def parse_matches(tid):
    url = BASE_TOURNEY_URL + tid
    soup = get_soup(url)

    if not soup:
        return []

    matches = []

    for row in soup.find_all("tr"):
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        try:
            round_name = cols[0].get_text(strip=True)
            p1 = cols[1].get_text(strip=True)
            p2 = cols[2].get_text(strip=True)
            score = cols[3].get_text(strip=True)

            if not p1 or not p2:
                continue

            matches.append({
                "round": round_name,
                "player1": p1,
                "player2": p2,
                "score": score,
                "winner": p1
            })

        except:
            continue

    return matches


# -----------------------------
# PROCESS YEAR
# -----------------------------
def process_year(year):
    print(f"\nYEAR {year}")

    tournaments = get_tournaments(year)

    print(f"Found {len(tournaments)} tournaments")

    year_data = []

    for t in tournaments:
        print(f"  {t['name']} ({t['id']})")

        matches = parse_matches(t["id"])

        if not matches:
            continue

        year_data.append({
            "tournament_id": t["id"],
            "name": t["name"],
            "matches": matches
        })

        time.sleep(1)

    json.dump(
        year_data,
        open(f"{OUTPUT_DIR}/{year}.json", "w"),
        indent=2
    )


# -----------------------------
# MAIN
# -----------------------------
def main():
    for year in range(1968, 2027):
        process_year(year)


if __name__ == "__main__":
    main()
