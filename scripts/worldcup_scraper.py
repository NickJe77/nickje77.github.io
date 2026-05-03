import requests
from bs4 import BeautifulSoup
import os
import json
import time
import re

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

WORLD_CUP_KEYWORDS = [
    "world cup",
    "prudential",
    "reliance",
    "benson & hedges",
    "wills"
]

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
def parse_scorecard(match_id):

    url = f"http://www.howstat.com/Cricket/Statistics/Matches/MatchScorecard_ODI.asp?MatchCode={match_id:04d}"

    res = requests.get(url, headers=HEADERS)

    # skip dead pages
    if "Scorecard" not in res.text:
        return None

    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("h1")
    if not title:
        return None

    match_name = title.text.strip()

    # FILTER WORLD CUP
    if not any(k in match_name.lower() for k in WORLD_CUP_KEYWORDS):
        return None

    # extract year properly
    year = None
    match = re.search(r"(19|20)\d{2}", match_name)
    if match:
        year = match.group(0)
    else:
        year = "unknown"

    data = {
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

            data["innings"].append(current)

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

    return year, match_id, data

# -----------------------------
# BUILD
# -----------------------------
def build():

    total = 0

    # covers all ODI history
    for match_id in range(1, 20000):

        if match_id % 200 == 0:
            print(f"Checking {match_id}...")

        try:
            result = parse_scorecard(match_id)

            if not result:
                continue

            year, mid, data = result

            folder = f"{OUTPUT}/{year}"
            os.makedirs(folder, exist_ok=True)

            path = f"{folder}/{mid}.json"

            safe_write(path, data)

            print(f"Saved {mid}")
            total += 1

            time.sleep(0.2)

        except Exception as e:
            print("FAILED:", match_id, e)

    print(f"\nBuilt {total} matches")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    build()
    print("DONE")
