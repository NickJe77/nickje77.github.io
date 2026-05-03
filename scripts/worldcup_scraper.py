import requests
from bs4 import BeautifulSoup
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# World Cup IDs on Cricinfo
WORLD_CUPS = {
    "1975": "1",
    "1979": "2",
    "1983": "3",
    "1987": "4",
    "1992": "5",
    "1996": "6",
    "1999": "7",
    "2003": "8",
    "2007": "9",
    "2011": "10",
    "2015": "11",
    "2019": "12",
    "2023": "13"
}

# -----------------------------
# SAFE WRITE
# -----------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------------
# GET MATCH LINKS
# -----------------------------
def get_matches(series_id):

    url = f"https://stats.espncricinfo.com/ci/engine/series/{series_id}.html?view=results"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/engine/match/" in href:
            full = "https://www.espncricinfo.com" + href
            links.append(full)

    return list(set(links))

# -----------------------------
# PARSE SCORECARD
# -----------------------------
def parse_match(url):

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("title")
    match_name = title.text if title else ""

    match = {
        "match": match_name,
        "date": "",
        "venue": "",
        "result": "",
        "innings": []
    }

    # Cricinfo parsing is complex — start simple
    tables = soup.find_all("table")

    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all("th")]

        if "runs" in headers:

            inning = {
                "team": "Unknown",
                "batting": {},
                "bowling": {}
            }

            rows = table.find_all("tr")[1:]

            for r in rows:
                cols = [c.text.strip() for c in r.find_all("td")]

                if len(cols) < 3:
                    continue

                player = cols[0]
                runs = cols[2]

                if runs.isdigit():
                    inning["batting"][player] = {"runs": int(runs)}

            match["innings"].append(inning)

    return match

# -----------------------------
# BUILD
# -----------------------------
def build():

    total = 0

    for year, series_id in WORLD_CUPS.items():

        print(f"\n--- {year} ---")

        links = get_matches(series_id)

        print(f"{len(links)} matches found")

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for link in links:

            match_id = link.split("/")[-1].replace(".html", "")
            path = f"{folder}/{match_id}.json"

            if os.path.exists(path):
                continue

            try:
                data = parse_match(link)
                safe_write(path, data)

                print(f"Saved {match_id}")
                total += 1
                time.sleep(0.3)

            except Exception as e:
                print("FAILED:", link, e)

    print(f"\nBuilt {total} matches")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    build()
    print("DONE")
