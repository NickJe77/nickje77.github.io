import requests
from bs4 import BeautifulSoup
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------------------------
# SAFE WRITE
# --------------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# --------------------------------
# PARSE SCORECARD
# --------------------------------
def parse_scorecard(match_id):

    url = f"http://www.howstat.com/cricket/Statistics/Matches/MatchScorecard.asp?MatchCode={match_id}"
    res = requests.get(url, headers=HEADERS)

    # Skip invalid pages
    if "Scorecard" not in res.text:
        return None

    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("h1")
    if not title:
        return None

    match_name = title.text.strip()

    # ONLY WORLD CUP MATCHES
    if "World Cup" not in match_name:
        return None

    # Extract year from title
    year = None
    for part in match_name.split():
        if part.isdigit() and len(part) == 4:
            year = part
            break

    if not year:
        return None

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

        # ---------------- BATTING ----------------
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

        # ---------------- BOWLING ----------------
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

    return year, match_id, match

# --------------------------------
# MAIN
# --------------------------------
def build():

    total = 0

    print("Scanning Howstat match IDs...")

    # Wide range to guarantee coverage
    for match_id in range(1, 20000):

        try:
            result = parse_scorecard(match_id)

            if not result:
                continue

            year, mid, data = result

            folder = f"{OUTPUT}/{year}"
            os.makedirs(folder, exist_ok=True)

            path = f"{folder}/{mid}.json"

            if os.path.exists(path):
                continue

            safe_write(path, data)

            print(f"{year} -> Saved {mid}")
            total += 1

            time.sleep(0.2)

        except Exception as e:
            print("Error:", match_id, e)

    print(f"\nBuilt {total} World Cup matches")

if __name__ == "__main__":
    build()
