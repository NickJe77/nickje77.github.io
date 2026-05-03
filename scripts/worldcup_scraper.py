import requests
from bs4 import BeautifulSoup
import zipfile, io, os, json, time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

CRICSHEET_URL = "https://cricsheet.org/downloads/odis_json.zip"

VALID_EVENTS = [
    "ICC Cricket World Cup",
    "ICC World Cup",
    "Prudential World Cup",
    "Reliance World Cup",
    "Benson & Hedges World Cup",
    "Wills World Cup"
]

# --------------------------------
# SAFE WRITE
# --------------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# --------------------------------
# CRICSHEET (2000+)
# --------------------------------
def build_cricsheet():

    print("Downloading Cricsheet...")
    r = requests.get(CRICSHEET_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("tmp")

    built = 0

    for file in os.listdir("tmp"):

        if not file.endswith(".json"):
            continue

        with open(f"tmp/{file}") as f:
            data = json.load(f)

        info = data.get("info", {})
        event = info.get("event", {}).get("name", "")

        if not any(e in event for e in VALID_EVENTS):
            continue

        date = info.get("dates", [""])[0]
        year = date[:4]

        if int(year) < 2000:
            continue

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        match_id = file.replace(".json", "")
        path = f"{folder}/{match_id}.json"

        if os.path.exists(path):
            continue

        match = {
            "match": " vs ".join(info.get("teams", [])),
            "date": date,
            "venue": info.get("venue", ""),
            "result": info.get("outcome", {}),
            "innings": []
        }

        for inn in data.get("innings", []):
            team = list(inn.keys())[0]
            details = inn[team]

            inning = {"team": team, "batting": {}, "bowling": {}}
            deliveries = []

            if "overs" in details:
                for over in details["overs"]:
                    deliveries.extend(over.get("deliveries", []))
            else:
                deliveries = details.get("deliveries", [])

            for delivery in deliveries:
                for ball in delivery.values():

                    batter = ball.get("batter")
                    bowler = ball.get("bowler")
                    runs_b = ball.get("runs", {}).get("batter", 0)
                    runs_t = ball.get("runs", {}).get("total", 0)

                    if batter:
                        b = inning["batting"].setdefault(batter, {
                            "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "out": ""
                        })
                        b["runs"] += runs_b
                        b["balls"] += 1
                        if runs_b == 4: b["fours"] += 1
                        if runs_b == 6: b["sixes"] += 1

                    if bowler:
                        bl = inning["bowling"].setdefault(bowler, {
                            "runs": 0, "wickets": 0
                        })
                        bl["runs"] += runs_t

                    if "wickets" in ball:
                        for w in ball["wickets"]:
                            p = w.get("player_out")
                            if p and p in inning["batting"]:
                                inning["batting"][p]["out"] = w.get("kind", "")
                            if bowler:
                                inning["bowling"][bowler]["wickets"] += 1

            match["innings"].append(inning)

        safe_write(path, match)
        built += 1

    print(f"Cricsheet built: {built}")

# --------------------------------
# HOWSTAT (1975–1999)
# --------------------------------
def build_howstat():

    print("Building pre-2000...")

    total = 0

    for match_id in range(1000, 1300):

        url = f"http://www.howstat.com/cricket/Statistics/Matches/MatchScorecard.asp?MatchCode={match_id}"
        res = requests.get(url)

        if "Scorecard" not in res.text:
            continue

        soup = BeautifulSoup(res.text, "lxml")

        title = soup.find("h1")
        if not title:
            continue

        match_name = title.text

        # filter to world cups only
        if "World Cup" not in match_name:
            continue

        year = match_name[-4:]

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        path = f"{folder}/{match_id}.json"

        if os.path.exists(path):
            continue

        data = {
            "match": match_name,
            "date": "",
            "venue": "",
            "result": "",
            "innings": []
        }

        safe_write(path, data)
        total += 1
        time.sleep(0.3)

    print(f"Howstat built: {total}")

# --------------------------------
# MAIN
# --------------------------------
if __name__ == "__main__":
    build_cricsheet()
    build_howstat()
    print("DONE")
