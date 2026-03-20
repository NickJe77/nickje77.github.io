import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("AFL PLAYER SCRAPER — FIXED VERSION")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026

OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------
# HELPERS
# -----------------------------

def clean_int(val):
    try:
        return int(val.strip())
    except:
        return 0


def get_match_links():
    url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}"
    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        if "ft_match_statistics" in a["href"]:
            links.append(BASE + a["href"])

    return list(set(links))


def parse_match(url):

    print("Scraping:", url)

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    # -----------------------------
    # MATCH INFO
    # -----------------------------

    title = soup.find("title").text

    # Example:
    # "Sydney v Carlton - Round 0 - SCG"
    parts = title.split(" - ")

    teams = parts[0].split(" v ")
    team1 = teams[0].strip()
    team2 = teams[1].strip()

    round_name = parts[1] if len(parts) > 1 else ""
    venue = parts[2] if len(parts) > 2 else ""

    # -----------------------------
    # FIND CORRECT TABLES
    # -----------------------------

    tables = soup.find_all("table")

    player_tables = []

    for t in tables:
        if "Player" in t.text and "Disposals" in t.text:
            player_tables.append(t)

    # Usually 2 tables: one per team
    data = []

    for i, table in enumerate(player_tables):

        rows = table.find_all("tr")

        for row in rows:

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            # Skip header rows
            if "Player" in row.text:
                continue

            player_name = cols[0].text.strip()

            if player_name == "":
                continue

            player = {
                "player": player_name,
                "played_for": team1 if i == 0 else team2,
                "played_against": team2 if i == 0 else team1,
                "round": round_name,
                "venue": venue,
                "season": SEASON,

                "K": clean_int(cols[1].text),
                "HB": clean_int(cols[2].text),
                "D": clean_int(cols[3].text),
                "M": clean_int(cols[4].text),
                "G": clean_int(cols[5].text),
                "B": clean_int(cols[6].text),
                "T": clean_int(cols[7].text),
                "HO": clean_int(cols[8].text),
                "GA": clean_int(cols[9].text),
                "I50": clean_int(cols[10].text),
                "CL": clean_int(cols[11].text),
                "CG": clean_int(cols[12].text),
                "R50": clean_int(cols[13].text),
                "FF": clean_int(cols[14].text),
                "FA": clean_int(cols[15].text),
                "AF": clean_int(cols[16].text),
                "SC": clean_int(cols[17].text)
            }

            data.append(player)

    return data


# -----------------------------
# MAIN
# -----------------------------

all_matches = get_match_links()

print("Matches found:", len(all_matches))

all_data = []

for link in all_matches:
    try:
        match_data = parse_match(link)
        all_data.extend(match_data)
    except Exception as e:
        print("ERROR:", e)

# -----------------------------
# SAVE
# -----------------------------

with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("DONE — DATA SAVED:", OUTPUT)
