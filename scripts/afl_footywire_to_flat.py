import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRIPT VERSION 12 — FINAL FINAL (FORCED 2 TABLE FIX)")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026

OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -----------------------------
# SAFE STAT
# -----------------------------
def get_stat(cols, i):
    try:
        return int(cols[i].text.strip())
    except:
        return 0


# -----------------------------
# GET MATCH LINKS
# -----------------------------
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

    links = list(set(links))

    print("Matches found:", len(links))
    if links:
        print("Sample link:", links[0])

    return links


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→ Scraping:", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text
    title = title.replace("AFL Match Statistics : ", "")

    # -----------------------------
    # TEAM PARSING
    # -----------------------------
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

    # -----------------------------
    # ROUND + VENUE
    # -----------------------------
    round_name = ""
    venue = ""

    round_match = re.search(r"(Round \d+)", title)
    if round_match:
        round_name = round_match.group(1)

    venue_match = re.search(r" at ([A-Za-z0-9\s]+) Round", title)
    if venue_match:
        venue = venue_match.group(1).strip()

    # -----------------------------
    # FIND PLAYER TABLES
    # -----------------------------
    tables = soup.find_all("table")

    candidate_tables = []

    for table in tables:

        text = table.get_text(" ", strip=True)

        # Must contain stat headers
        if not all(x in text for x in ["K", "HB", "D", "M", "G"]):
            continue

        rows = table.find_all("tr")
        valid_rows = []

        for row in rows:
            cols = row.find_all("td")

            if len(cols) >= 5 and cols[0].find("a"):
                valid_rows.append(cols)

        # AFL = exactly 23 players
        if len(valid_rows) >= 20:
            candidate_tables.append(valid_rows)

    # 🔥 FINAL FIX: FORCE FIRST 2 ONLY
    player_tables = candidate_tables[:2]

    if len(player_tables) < 2:
        print("⚠️ Not enough player tables")
        return []

    # -----------------------------
    # PARSE PLAYERS
    # -----------------------------
    data = []

    for team_index, valid_rows in enumerate(player_tables):

        for cols in valid_rows[:23]:  # 🔥 HARD CAP

            player_name = cols[0].text.strip()

            entry = {
                "player": player_name,
                "played_for": team1 if team_index == 0 else team2,
                "played_against": team2 if team_index == 0 else team1,
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

        print(f"Players parsed (team {team_index+1}):", len(valid_rows[:23]))

    return data


# -----------------------------
# RUN
# -----------------------------
links = get_links()

all_data = []

for link in links:
    try:
        all_data.extend(parse_match(link))
    except Exception as e:
        print("ERROR:", e)

print("TOTAL RECORDS:", len(all_data))


# -----------------------------
# SAVE
# -----------------------------
with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("DONE — SAVED TO:", OUTPUT.resolve())
