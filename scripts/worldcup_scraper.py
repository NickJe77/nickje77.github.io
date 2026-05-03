import os
import json
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

WORLD_CUP_KEYWORDS = [
    "World Cup",
    "Prudential",
    "Reliance",
    "Benson & Hedges",
    "Wills"
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
# SETUP DRIVER
# -----------------------------
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    return driver

# -----------------------------
# PARSE SCORECARD (UNCHANGED LOGIC)
# -----------------------------
def parse_scorecard(driver, url):

    driver.get(url)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "lxml")

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
# BUILD
# -----------------------------
def build():

    driver = get_driver()
    total = 0

    for year in range(1975, 2024):

        print(f"\n--- {year} ---")

        url = f"http://www.howstat.com/cricket/Statistics/Matches/MatchList.asp?Stat=ODI;Year={year}"
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "lxml")
        rows = soup.find_all("tr")

        print("Rows:", len(rows))

        links = []

        for r in rows:

            text = r.text

            if not any(k.lower() in text.lower() for k in WORLD_CUP_KEYWORDS):
                continue

            a = r.find("a", href=True)

            if a and "MatchScorecard" in a["href"]:
                links.append("http://www.howstat.com" + a["href"])

        print(f"{len(links)} matches found")

        if not links:
            continue

        folder = f"{OUTPUT}/{year}"
        os.makedirs(folder, exist_ok=True)

        for link in links:

            match_id = link.split("=")[-1]
            path = f"{folder}/{match_id}.json"

            if os.path.exists(path):
                continue

            try:
                data = parse_scorecard(driver, link)
                safe_write(path, data)

                print(f"Saved {match_id}")
                total += 1
                time.sleep(0.5)

            except Exception as e:
                print("FAILED:", link, e)

    driver.quit()
    print(f"\nBuilt {total} matches")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    build()
    print("DONE")
