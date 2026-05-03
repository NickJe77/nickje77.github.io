import requests
from bs4 import BeautifulSoup
import os
import json
import time

BASE = "docs/data/cricket/world_cups"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def parse_scorecard(match_id):

    url = f"https://www.howstat.com/Cricket/Statistics/Matches/MatchScoreCard_ODI.asp?MatchCode={match_id:04d}"

    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, "lxml")

    tables = soup.find_all("table")
    innings = []
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
                runs = cols[2]

                if runs.isdigit():
                    current["batting"][player] = {
                        "runs": int(runs),
                        "balls": int(cols[3]) if cols[3].isdigit() else 0,
                        "fours": int(cols[4]) if cols[4].isdigit() else 0,
                        "sixes": int(cols[5]) if len(cols) > 5 and cols[5].isdigit() else 0
                    }

            innings.append(current)

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

    return innings

def run():

    total = 0

    for year in os.listdir(BASE):

        folder = os.path.join(BASE, year)

        if not os.path.isdir(folder):
            continue

        print(f"\n--- {year} ---")

        for file in os.listdir(folder):

            if not file.endswith(".json"):
                continue

            path = os.path.join(folder, file)

            data = load_json(path)

            # skip already filled matches
            if data.get("innings"):
                continue

            match_id = int(file.replace(".json", ""))

            try:
                innings = parse_scorecard(match_id)

                if not innings:
                    continue

                data["innings"] = innings

                save_json(path, data)

                print(f"Updated {match_id}")
                total += 1

                time.sleep(0.3)

            except Exception as e:
                print("FAILED:", match_id, e)

    print(f"\nUpdated {total} matches")

if __name__ == "__main__":
    run()
    print("DONE")
