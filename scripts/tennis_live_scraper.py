import requests
from bs4 import BeautifulSoup
import json
import os
import time

OUTPUT_DIR = "docs/data/tennis/matches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -----------------------------
# GENERIC GET
# -----------------------------
def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except:
        return None
    return None


# -----------------------------
# SOURCE 1 — TENNIS EXPLORER
# -----------------------------
def scrape_tennisexplorer(year):

    print(f"[TE] {year}")

    url = f"https://www.tennisexplorer.com/results/?year={year}"
    soup = get_soup(url)

    matches = []

    if not soup:
        return matches

    for row in soup.select("tr"):
        cols = row.find_all("td")

        if len(cols) < 5:
            continue

        try:
            player1 = cols[2].text.strip()
            player2 = cols[3].text.strip()
            score = cols[4].text.strip()

            matches.append({
                "player1": player1,
                "player2": player2,
                "score": score,
                "year": year
            })
        except:
            continue

    return matches


# -----------------------------
# SOURCE 2 — TENNIS ABSTRACT (BACKUP)
# -----------------------------
def scrape_tennisabstract(year):

    print(f"[TA] {year}")

    base = f"https://r.jina.ai/http://www.tennisabstract.com/cgi-bin/tourneys.cgi?year={year}"
    soup = get_soup(base)

    matches = []

    if not soup:
        return matches

    for a in soup.find_all("a"):
        href = a.get("href","")
        if "tourney.cgi?t=" in href:

            tid = href.split("t=")[-1]

            t_url = f"https://r.jina.ai/http://www.tennisabstract.com/cgi-bin/tourney.cgi?t={tid}"
            t_soup = get_soup(t_url)

            if not t_soup:
                continue

            for row in t_soup.find_all("tr"):
                cols = row.find_all("td")

                if len(cols) < 4:
                    continue

                try:
                    matches.append({
                        "round": cols[0].text.strip(),
                        "player1": cols[1].text.strip(),
                        "player2": cols[2].text.strip(),
                        "score": cols[3].text.strip(),
                        "year": year
                    })
                except:
                    continue

            time.sleep(0.5)

    return matches


# -----------------------------
# MERGE + DEDUPE
# -----------------------------
def merge_matches(primary, backup):

    seen = set()
    out = []

    for m in primary + backup:
        key = (m.get("player1"), m.get("player2"), m.get("score"))

        if key in seen:
            continue

        seen.add(key)
        out.append(m)

    return out


# -----------------------------
# SAVE
# -----------------------------
def save_year(year, matches):

    path = f"{OUTPUT_DIR}/{year}.json"

    if os.path.exists(path):
        existing = json.load(open(path))
    else:
        existing = []

    combined = merge_matches(existing, matches)

    json.dump(combined, open(path,"w"), indent=2)

    print(f"{year} saved ({len(combined)})")


# -----------------------------
# MAIN
# -----------------------------
def main():

    for year in [2025, 2026]:

        te = scrape_tennisexplorer(year)
        ta = scrape_tennisabstract(year)

        merged = merge_matches(te, ta)

        save_year(year, merged)


if __name__ == "__main__":
    main()
