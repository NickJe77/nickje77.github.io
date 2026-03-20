import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRIPT VERSION 14 — FINAL (NO HREF CRASH)")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026

OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def get_stat(cols, i):
    try:
        return int(cols[i].text.strip())
    except:
        return 0


def get_links():
    url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "ft_match_statistics" not in href:
            continue

        if href.startswith("http"):
            link = href
        elif href.startswith("/"):
            link = BASE + href
        else:
            link = BASE + "/afl/footy/" + href

        links.append(link)

    return list(set(links))


def extract_team_from_link(link):
    if not link or "pp-" not in link:
        return ""

    part = link.split("pp-")[1]
    return part.split("-")[0].lower()


def normalize(name):
    return name.lower().replace(" ", "")


def parse_match(url):

    print("→ Scraping:", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text.replace("AFL Match Statistics : ", "")

    # TEAM PARSING
    if " v " in title:
        t = title.split(" v ")
        team1, team2 = t[0].strip(), t[1].split(" ")[0].strip()

    elif " defeated by " in title:
        t = title.split(" defeated by ")
        team1, team2 = t[0].strip(), t[1].split(" at ")[0].strip()

    elif " defeats " in title:
        t = title.split(" defeats ")
        team1, team2 = t[0].strip(), t[1].split(" at ")[0].strip()

    elif " defeat " in title:
        t = title.split(" defeat ")
        team1, team2 = t[0].strip(), t[1].split(" at ")[0].strip()

    elif " defeated " in title:
        t = title.split(" defeated ")
        team1, team2 = t[0].strip(), t[1].split(" at ")[0].strip()

    else:
        print("⚠️ Could not parse teams:", title)
        return []

    team1_key = normalize(team1)
    team2_key = normalize(team2)

    # ROUND + VENUE
    round_name = ""
    venue = ""

    r = re.search(r"(Round \d+)", title)
    if r:
        round_name = r.group(1)

    v = re.search(r" at ([A-Za-z0-9\s]+) Round", title)
    if v:
        venue = v.group(1).strip()

    tables = soup.find_all("table")

    team_tables = {team1_key: None, team2_key: None}

    for table in tables:

        text = table.get_text(" ", strip=True)

        if not all(x in text for x in ["K", "HB", "D", "M", "G"]):
            continue

        rows = table.find_all("tr")

        valid_rows = []

        for row in rows:
            cols = row.find_all("td")

            if len(cols) >= 5:
                a = cols[0].find("a")
                if a:
                    valid_rows.append(cols)

        if len(valid_rows) < 20:
            continue

        # 🔥 SAFE LINK EXTRACTION
        first_a = valid_rows[0][0].find("a")

        if not first_a or not first_a.has_attr("href"):
            continue

        team_guess = extract_team_from_link(first_a["href"])

        if team1_key in team_guess:
            team_tables[team1_key] = valid_rows

        elif team2_key in team_guess:
            team_tables[team2_key] = valid_rows

    if not team_tables[team1_key] or not team_tables[team2_key]:
        print("⚠️ Failed to match both teams")
        return []

    data = []

    for team_key, rows in team_tables.items():

        for cols in rows[:23]:

            entry = {
                "player": cols[0].text.strip(),
                "played_for": team1 if team_key == team1_key else team2,
                "played_against": team2 if team_key == team1_key else team1,
                "round": round_name,
                "venue": venue,
                "season": SEASON,

                "K": get_stat(cols, 1),
                "HB": get_stat(cols, 2),
                "D": get_stat(cols, 3),
                "M": get_stat(cols, 4),
                "G": get_stat(cols, 5),
                "B": get_stat(cols, 6),
                "T": get_stat(cols, 7),
                "HO": get_stat(cols, 8),
                "GA": get_stat(cols, 9),
                "I50": get_stat(cols, 10),
                "CL": get_stat(cols, 11),
                "CG": get_stat(cols, 12),
                "R50": get_stat(cols, 13),
                "FF": get_stat(cols, 14),
                "FA": get_stat(cols, 15),
                "AF": get_stat(cols, 16),
                "SC": get_stat(cols, 17)
            }

            data.append(entry)

        print(f"{team_key}: {len(rows[:23])} players")

    return data


# RUN
links = get_links()

all_data = []

for link in links:
    try:
        all_data.extend(parse_match(link))
    except Exception as e:
        print("ERROR:", e)

print("TOTAL:", len(all_data))

with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("DONE")
