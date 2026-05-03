import requests
from bs4 import BeautifulSoup
import zipfile, io, os, json, time, re

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------------------------------
# UTIL
# ---------------------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def year_from_date(date_str):
    return date_str[:4] if date_str else "unknown"

# ---------------------------------------
# 1) CRICSHEET (2000+ FULL DETAIL)
# ---------------------------------------
def build_from_cricsheet():
    url = "https://cricsheet.org/downloads/odis_json.zip"
    print("Downloading Cricsheet…")
    r = requests.get(url, timeout=60)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("cricsheet_tmp")

    built = 0

    for file in os.listdir("cricsheet_tmp"):
        if not file.endswith(".json"):
            continue

        path = os.path.join("cricsheet_tmp", file)
        with open(path) as f:
            data = json.load(f)

        info = data.get("info", {})
        event = info.get("event", {}).get("name", "")

        if "World Cup" not in event:
            continue

        date = info.get("dates", [""])[0]
        year = year_from_date(date)

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        match_id = file.replace(".json", "")
        out = f"{folder}/{match_id}.json"

        if os.path.exists(out):
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

            for over in details.get("overs", []):
                for delivery in over.get("deliveries", []):
                    for ball in delivery.values():
                        batter = ball.get("batter")
                        bowler = ball.get("bowler")
                        runs_b = ball.get("runs", {}).get("batter", 0)
                        runs_t = ball.get("runs", {}).get("total", 0)

                        # batting
                        if batter:
                            b = inning["batting"].setdefault(batter, {
                                "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "out": ""
                            })
                            b["runs"] += runs_b
                            b["balls"] += 1
                            if runs_b == 4: b["fours"] += 1
                            if runs_b == 6: b["sixes"] += 1

                        # bowling
                        if bowler:
                            bl = inning["bowling"].setdefault(bowler, {
                                "runs": 0, "wickets": 0
                            })
                            bl["runs"] += runs_t

                        # wickets
                        if "wickets" in ball:
                            for w in ball["wickets"]:
                                out_p = w.get("player_out")
                                kind = w.get("kind", "")
                                if out_p and out_p in inning["batting"]:
                                    inning["batting"][out_p]["out"] = kind
                                if bowler:
                                    inning["bowling"][bowler]["wickets"] += 1

            match["innings"].append(inning)

        safe_write(out, match)
        built += 1

    print(f"Cricsheet built: {built}")

# ---------------------------------------
# 2) HOWSTAT (1975–1999 FULL SCORECARDS)
# ---------------------------------------
# NOTE: Howstat pages are stable tables. We:
# - list matches by year
# - open each scorecard
# - parse batting & bowling tables

HOWSTAT_LIST = "http://www.howstat.com/cricket/Statistics/Matches/MatchList.asp?Stat=ODI;Series=ICC%20World%20Cup;Year={year}"

def parse_howstat_scorecard(url):
    res = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")

    # header
    title = soup.find("h1")
    match_name = title.text.strip() if title else ""

    # date / venue
    meta = soup.find_all("td")
    date = ""
    venue = ""
    for td in meta:
        txt = td.text.strip()
        if re.match(r"\d{1,2}\s\w+\s\d{4}", txt):
            date = txt
        if "Ground:" in txt or "Venue:" in txt:
            venue = txt.split(":")[-1].strip()

    innings = []

    # Howstat uses repeated tables; detect by headers
    tables = soup.find_all("table")

    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all("th")]

        # batting table
        if "runs" in headers and "balls" in headers:
            team = table.find_previous("h2")
            team_name = team.text.strip() if team else ""

            batting = {}
            rows = table.find_all("tr")[1:]

            for r in rows:
                cols = [c.text.strip() for c in r.find_all("td")]
                if len(cols) < 5:
                    continue

                player = cols[0]
                dismissal = cols[1]
                runs = cols[2]

                if runs.isdigit():
                    batting[player] = {
                        "runs": int(runs),
                        "balls": int(cols[3]) if cols[3].isdigit() else 0,
                        "fours": int(cols[4]) if cols[4].isdigit() else 0,
                        "sixes": int(cols[5]) if len(cols) > 5 and cols[5].isdigit() else 0,
                        "out": dismissal
                    }

            innings.append({"team": team_name, "batting": batting, "bowling": {}})

        # bowling table
        if "wickets" in headers and "overs" in headers:
            rows = table.find_all("tr")[1:]
            bowling = {}

            for r in rows:
                cols = [c.text.strip() for c in r.find_all("td")]
                if len(cols) < 5:
                    continue

                player = cols[0]
                runs = cols[2]
                wkts = cols[3]

                if runs.isdigit() and wkts.isdigit():
                    bowling[player] = {
                        "runs": int(runs),
                        "wickets": int(wkts)
                    }

            # attach to last innings parsed
            if innings:
                innings[-1]["bowling"] = bowling

    return {
        "match": match_name,
        "date": date,
        "venue": venue,
        "result": "",  # can be extended if needed
        "innings": innings
    }

def build_from_howstat():
    built = 0

    for year in range(1975, 2000):
        url = HOWSTAT_LIST.format(year=year)
        res = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        # match links
        links = []
        for a in soup.find_all("a", href=True):
            if "Scorecard" in a.text:
                links.append("http://www.howstat.com" + a["href"])

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for link in links:
            match_id = link.split("=")[-1]
            out = f"{folder}/{match_id}.json"

            if os.path.exists(out):
                continue

            try:
                data = parse_howstat_scorecard(link)
                safe_write(out, data)
                built += 1
                time.sleep(0.5)
            except Exception as e:
                print("FAIL", link, e)

    print(f"Howstat built: {built}")

# ---------------------------------------
# MAIN
# ---------------------------------------
if __name__ == "__main__":
    build_from_cricsheet()   # 2000+
    build_from_howstat()     # 1975–1999
    print("Done.")
