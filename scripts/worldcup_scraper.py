import requests
from bs4 import BeautifulSoup
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ----------------------------------------
# KNOWN WORLD CUP MATCH IDS (STARTER SET)
# ----------------------------------------
# (These are stable on Howstat — we expand from here)
WORLD_CUP_MATCH_IDS = {
    1975: list(range(1000, 1015)),   # placeholder range (will auto-skip invalid)
    1979: list(range(1016, 1030)),
    1983: list(range(1031, 1060)),
    1987: list(range(1061, 1100)),
    1992: list(range(1101, 1150)),
    1996: list(range(1151, 1200)),
    1999: list(range(1201, 1250))
}

# ----------------------------------------
# SAFE WRITE
# ----------------------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ----------------------------------------
# PARSE SCORECARD
# ----------------------------------------
def parse_scorecard(match_id):

    url = f"http://www.howstat.com/cricket/Statistics/Matches/MatchScorecard.asp?MatchCode={match_id}"
    res = requests.get(url, headers=HEADERS)

    # Skip invalid pages
    if "Scorecard" not in res.text:
        return None

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

# ----------------------------------------
# MAIN
# ----------------------------------------
def build():

    total = 0

    for year, ids in WORLD_CUP_MATCH_IDS.items():

        print(f"\n--- {year} ---")

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for match_id in ids:

            file_path = f"{folder}/{match_id}.json"

            if os.path.exists(file_path):
                continue

            try:
                data = parse_scorecard(match_id)

                if not data:
                    continue

                safe_write(file_path, data)

                print(f"Saved {match_id}")
                total += 1
                time.sleep(0.3)

            except Exception as e:
                print("FAILED:", match_id, e)

    print(f"\nBuilt {total} matches")

if __name__ == "__main__":
    build()
