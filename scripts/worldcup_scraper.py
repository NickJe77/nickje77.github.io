import requests
from bs4 import BeautifulSoup
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

SERIES = {
    1975: 17,
    1979: 18,
    1983: 19,
    1987: 20,
    1992: 21,
    1996: 22,
    1999: 23,
    2003: 24,
    2007: 25,
    2011: 26,
    2015: 27,
    2019: 28,
    2023: 29
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
# PARSE SCORECARD
# -----------------------------
def parse_scorecard(url):

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("h1")
    match_name = title.text.strip() if title else ""

    match = {
        "match": match_name,
        "date": "",
        "venue": "",
        "result": "",
        "innings": []
    }

    tables = soup.find_all("table")
    current = None

    for table in tables:

        headers = [th.text.strip().lower() for th in table.find_all("th")]

        # Batting
        if "runs" in headers and "balls" in headers:

            team_tag = table.find_previous("h2")
            team = team_tag.text.strip() if team_tag else "Unknown"

            current = {
                "team": team,
                "batting": {},
                "bowling": {}
            }

            rows = table.find_all("tr")[1:]

            for r in rows:
                cols = [c.text.strip() for c in r.find_all("td")]

                if len(cols) < 5:
                    continue

                player = cols[0]
                dismissal = cols[1]
                runs = cols[2]

                if runs.isdigit():
                    current["batting"][player] = {
                        "runs": int(runs),
                        "balls": int(cols[3]) if cols[3].isdigit() else 0,
                        "fours": int(cols[4]) if cols[4].isdigit() else 0,
                        "sixes": int(cols[5]) if len(cols) > 5 and cols[5].isdigit() else 0,
                        "out": dismissal
                    }

            match["innings"].append(current)

        # Bowling
        if "wickets" in headers and current:

            rows = table.find_all("tr")[1:]

            for r in rows:
                cols = [c.text.strip() for c in r.find_all("td")]

                if len(cols) < 4:
                    continue

                player = cols[0]
                runs = cols[2]
                wkts = cols[3]

                if runs.isdigit() and wkts.isdigit():
                    current["bowling"][player] = {
                        "runs": int(runs),
                        "wickets": int(wkts)
                    }

    return match

# -----------------------------
# MAIN BUILD
# -----------------------------
def build():

    total = 0

    for year, code in SERIES.items():

        print(f"\n--- {year} ---")

        url = f"http://www.howstat.com/cricket/Statistics/Series/SeriesMatches.asp?SeriesCode={code}"
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "lxml")

        links = []

        for a in soup.find_all("a", href=True):
            if "MatchScorecard" in a["href"]:
                links.append("http://www.howstat.com" + a["href"])

        print(f"{len(links)} matches found")

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for link in links:

            match_id = link.split("=")[-1]
            path = f"{folder}/{match_id}.json"

            if os.path.exists(path):
                continue

            try:
                data = parse_scorecard(link)
                safe_write(path, data)

                print(f"Saved {match_id}")
                total += 1
                time.sleep(0.5)

            except Exception as e:
                print("FAILED:", link, e)

    print(f"\nBuilt {total} matches")

if __name__ == "__main__":
    build()
    print("DONE")
