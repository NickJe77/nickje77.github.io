import requests
from bs4 import BeautifulSoup
import os
import json
import time
import re

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

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

    res = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("h1")
    match_name = title.text.strip() if title else ""

    data = {
        "match": match_name,
        "date": "",
        "venue": "",
        "result": "",
        "innings": []
    }

    tables = soup.find_all("table")

    current_innings = None

    for table in tables:

        headers = [th.text.strip().lower() for th in table.find_all("th")]

        # -----------------------------
        # BATTING TABLE
        # -----------------------------
        if "runs" in headers and "balls" in headers:

            team_tag = table.find_previous("h2")
            team = team_tag.text.strip() if team_tag else "Unknown"

            current_innings = {
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
                    current_innings["batting"][player] = {
                        "runs": int(runs),
                        "balls": int(cols[3]) if cols[3].isdigit() else 0,
                        "fours": int(cols[4]) if cols[4].isdigit() else 0,
                        "sixes": int(cols[5]) if len(cols) > 5 and cols[5].isdigit() else 0,
                        "out": dismissal
                    }

            data["innings"].append(current_innings)

        # -----------------------------
        # BOWLING TABLE
        # -----------------------------
        if "wickets" in headers and "overs" in headers and current_innings:

            rows = table.find_all("tr")[1:]

            for r in rows:
                cols = [c.text.strip() for c in r.find_all("td")]

                if len(cols) < 5:
                    continue

                player = cols[0]
                runs = cols[2]
                wkts = cols[3]

                if runs.isdigit() and wkts.isdigit():
                    current_innings["bowling"][player] = {
                        "runs": int(runs),
                        "wickets": int(wkts)
                    }

    return data

# -----------------------------
# BUILD WORLD CUPS
# -----------------------------
def build_world_cups():

    total = 0

    for year in range(1975, 2000):

        print(f"\n--- {year} ---")

        list_url = f"http://www.howstat.com/cricket/Statistics/Matches/MatchList.asp?Stat=ODI;Year={year}"
        res = requests.get(list_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "lxml")

        links = []

        for a in soup.find_all("a", href=True):
            if "Scorecard" in a.text:
                links.append("http://www.howstat.com" + a["href"])

        print(f"{len(links)} matches found")

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for link in links:

            match_id = link.split("=")[-1]
            file_path = f"{folder}/{match_id}.json"

            if os.path.exists(file_path):
                continue

            try:
                match_data = parse_scorecard(link)
                safe_write(file_path, match_data)

                print(f"Saved {match_id}")
                total += 1
                time.sleep(0.5)

            except Exception as e:
                print("FAILED:", link, e)

    print(f"\nBuilt {total} matches")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    build_world_cups()
    print("Done.")
