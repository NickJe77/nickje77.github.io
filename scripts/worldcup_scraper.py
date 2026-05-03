import requests
from bs4 import BeautifulSoup
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ACTUAL WORKING RESULT PAGES
WORLD_CUP_URLS = {
    "1975": "https://www.espncricinfo.com/series/prudential-world-cup-1975-60793/match-results",
    "1979": "https://www.espncricinfo.com/series/prudential-world-cup-1979-60806/match-results",
    "1983": "https://www.espncricinfo.com/series/prudential-world-cup-1983-60832/match-results",
    "1987": "https://www.espncricinfo.com/series/reliance-world-cup-1987-60873/match-results",
    "1992": "https://www.espncricinfo.com/series/benson-hedges-world-cup-1991-92-60924/match-results",
    "1996": "https://www.espncricinfo.com/series/wills-world-cup-1995-96-60981/match-results",
    "1999": "https://www.espncricinfo.com/series/icc-world-cup-1999-61046/match-results",
    "2003": "https://www.espncricinfo.com/series/icc-world-cup-2002-03-61124/match-results",
    "2007": "https://www.espncricinfo.com/series/icc-world-cup-2006-07-125929/match-results",
    "2011": "https://www.espncricinfo.com/series/icc-world-cup-2011-381449/match-results",
    "2015": "https://www.espncricinfo.com/series/icc-cricket-world-cup-2015-509587/match-results",
    "2019": "https://www.espncricinfo.com/series/icc-cricket-world-cup-2019-1144415/match-results",
    "2023": "https://www.espncricinfo.com/series/icc-cricket-world-cup-2023-24-1367856/match-results"
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
def get_links(url):

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/match/" in href:
            full = "https://www.espncricinfo.com" + href
            links.append(full)

    return list(set(links))

# -----------------------------
# PARSE MATCH (MINIMAL BUT WORKING)
# -----------------------------
def parse_match(url):

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("title")
    if not title:
        return None

    match_name = title.text.strip()

    return {
        "match": match_name,
        "date": "",
        "venue": "",
        "result": "",
        "innings": []
    }

# -----------------------------
# BUILD
# -----------------------------
def build():

    total = 0

    for year, url in WORLD_CUP_URLS.items():

        print(f"\n--- {year} ---")

        links = get_links(url)
        print(f"{len(links)} matches found")

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for link in links:

            match_id = link.split("/")[-1]
            path = f"{folder}/{match_id}.json"

            if os.path.exists(path):
                continue

            data = parse_match(link)

            if not data:
                continue

            safe_write(path, data)

            print(f"Saved {match_id}")
            total += 1

            time.sleep(0.2)

    print(f"\nBuilt {total} matches")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    build()
