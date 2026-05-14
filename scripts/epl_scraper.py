import undetected_chromedriver as uc
from bs4 import BeautifulSoup, Comment
import json
import os
import time
import random
import re

BASE = "https://fbref.com"

SEASON_DIR = "docs/data/epl/seasons"
MATCH_DIR = "docs/data/epl/matches"

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(MATCH_DIR, exist_ok=True)

MIN_SLEEP = 5
MAX_SLEEP = 9

# =========================================================
# DRIVER
# =========================================================

def make_driver():

    options = uc.ChromeOptions()

    options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_argument("--window-size=1400,1000")

    driver = uc.Chrome(
        version_main=147,
        use_subprocess=True,
        options=options
    )

    driver.set_page_load_timeout(120)

    return driver

DRIVER = make_driver()

# =========================================================
# GET HTML
# =========================================================

def get_html(url):

    global DRIVER

    while True:

        try:

            DRIVER.get(url)

            time.sleep(random.uniform(6, 9))

            html = DRIVER.page_source

            if not html.strip():
                raise Exception("blank html")

            if "verify you are human" in html.lower():

                print("BLOCKED")

                time.sleep(60)

                continue

            return html

        except Exception as e:

            print("RESTARTING DRIVER")
            print(e)

            try:
                DRIVER.quit()
            except:
                pass

            time.sleep(5)

            DRIVER = make_driver()

# =========================================================
# TABLE
# =========================================================

def get_schedule_table(soup):

    for table in soup.find_all("table"):

        tid = table.get("id", "")

        if (
            tid.startswith("sched_")
            and "_9_1" in tid
        ):
            return table

    comments = soup.find_all(
        string=lambda text: isinstance(text, Comment)
    )

    for c in comments:

        if "sched_" not in c:
            continue

        csoup = BeautifulSoup(c, "html.parser")

        for table in csoup.find_all("table"):

            tid = table.get("id", "")

            if (
                tid.startswith("sched_")
                and "_9_1" in tid
            ):
                return table

    return None

# =========================================================
# CLEAN
# =========================================================

def clean_text(text):

    return re.sub(
        r"\s+",
        " ",
        text or ""
    ).strip()

def clean_minute(text):

    if not text:
        return None

    m = re.search(r"(\d+)", text)

    if not m:
        return None

    return int(m.group(1))

# =========================================================
# PARSE MATCH
# =========================================================

def parse_match(soup):

    data = {
        "home_team": "",
        "away_team": "",
        "home_score": None,
        "away_score": None,
        "scorers": [],
        "yellow_cards": [],
        "red_cards": []
    }

    scorebox = soup.find(
        "div",
        class_="scorebox"
    )

    if not scorebox:
        return data

    # =====================================================
    # TEAMS
    # =====================================================

    team_blocks = scorebox.find_all(
        "div",
        class_="team"
    )

    teams = []

    for block in team_blocks:

        a = block.find("a")

        if a:

            name = clean_text(
                a.get_text(
                    " ",
                    strip=True
                )
            )

            if name:
                teams.append(name)

    if len(teams) >= 2:

        data["home_team"] = teams[0]
        data["away_team"] = teams[1]

    # =====================================================
    # SCORE
    # =====================================================

    scores = scorebox.find_all(
        "div",
        class_="score"
    )

    if len(scores) >= 2:

        try:

            data["home_score"] = int(
                scores[0].get_text(
                    strip=True
                )
            )

            data["away_score"] = int(
                scores[1].get_text(
                    strip=True
                )
            )

        except:
            pass

    # =====================================================
    # EVENTS
    # =====================================================

    seen_goals = set()
    seen_yellows = set()
    seen_reds = set()

    event_divs = soup.find_all(
        "div",
        class_=re.compile(r"\bevent\b")
    )

    for ev in event_divs:

        text = clean_text(
            ev.get_text(
                " ",
                strip=True
            )
        )

        lower = text.lower()

        minute = clean_minute(text)

        if minute is None:
            continue

        links = ev.find_all("a")

        if not links:
            continue

        player = clean_text(
            links[0].get_text(
                " ",
                strip=True
            )
        )

        if not player:
            continue

        # =================================================
        # TEAM
        # =================================================

        team = ""

        classes = [
            c.lower()
            for c in ev.get("class", [])
        ]

        if "a" in classes:
            team = data["home_team"]

        elif "b" in classes:
            team = data["away_team"]

        # =================================================
        # GOALS
        # =================================================

        if (
            "goal" in lower
            or "penalty" in lower
            or "own goal" in lower
        ):

            key = (
                player,
                minute,
                team
            )

            if key not in seen_goals:

                seen_goals.add(key)

                data["scorers"].append({
                    "player": player,
                    "team": team,
                    "minute": minute,
                    "penalty": (
                        "penalty" in lower
                        or "(pen)" in lower
                    ),
                    "own_goal": (
                        "own goal" in lower
                    )
                })

        # =================================================
        # YELLOWS
        # =================================================

        if (
            "yellow card" in lower
            or "2nd yellow card" in lower
        ):

            key = (
                player,
                minute,
                team
            )

            if key not in seen_yellows:

                seen_yellows.add(key)

                data["yellow_cards"].append({
                    "player": player,
                    "team": team,
                    "minute": minute
                })

        # =================================================
        # REDS
        # =================================================

        red_terms = [
            "red card",
            "straight red",
            "second yellow red",
            "2nd yellow red"
        ]

        if any(
            term in lower
            for term in red_terms
        ):

            key = (
                player,
                minute,
                team
            )

            if key not in seen_reds:

                seen_reds.add(key)

                data["red_cards"].append({
                    "player": player,
                    "team": team,
                    "minute": minute
                })

    return data

# =========================================================
# START
# =========================================================

SEASONS = {}

for start_year in range(1992, 2026):

    end_year = start_year + 1

    season = f"{start_year}-{end_year}"

    SEASONS[season] = (
        f"https://fbref.com/en/comps/9/"
        f"{season}/schedule/"
        f"{season}-Premier-League-Scores-and-Fixtures"
    )

for season, season_url in SEASONS.items():

    print(f"\nBUILDING {season}")

    html = get_html(season_url)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = get_schedule_table(soup)

    if not table:
        print("NO TABLE")
        continue

    tbody = table.find("tbody")

    if not tbody:
        continue

    os.makedirs(
        f"{MATCH_DIR}/{season}",
        exist_ok=True
    )

    count = 1

    for row in tbody.find_all("tr"):

        report = row.find(
            "td",
            {"data-stat": "match_report"}
        )

        if not report:
            continue

        a = report.find(
            "a",
            href=True
        )

        if not a:
            continue

        match_url = BASE + a["href"]

        print("SCRAPING", match_url)

        try:

            html = get_html(match_url)

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            data = parse_match(soup)

            data["url"] = match_url

            with open(
                f"{MATCH_DIR}/{season}/{season}_{count:04d}.json",
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    indent=2
                )

            count += 1

        except Exception as e:

            print("FAILED", e)

        time.sleep(
            random.uniform(
                MIN_SLEEP,
                MAX_SLEEP
            )
        )

try:
    DRIVER.quit()
except:
    pass

print("\nDONE")
