import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("AFL SCRAPER — VERSION 4 (URL FIX)")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026

OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def to_int(x):
    try:
        return int(x.strip())
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
        if "ft_match_statistics" in a["href"]:
            link = BASE + "/" + a["href"].lstrip("/")
            links.append(link)

    links = list(set(links))

    print("Matches found:", len(links))

    return links


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→ Scraping:", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text
    parts = title.split(" - ")

    teams = parts[0].split(" v ")
    team1 = teams[0].strip()
    team2 = teams[1].strip()

    round_name = parts[1] if len(parts) > 1 else ""
    venue = parts[2] if len(parts) > 2 else ""

    tables = soup.find_all("table")

    data = []
    team_index = 0

    for table in tables:

        rows = table.find_all("tr")

        valid_rows = []

        for row in rows:
            cols = row.find_all("td")

            if len(cols) >= 10 and cols[0].find("a"):
                valid_rows.append(cols)

        if not valid_rows:
            continue

        for cols in valid_rows:

            player_name = cols[0].text.strip()

            entry = {
                "player": player_name,
                "played_for": team1 if team_index == 0 else team2,
                "played_against": team2 if team_index == 0 else team1,
                "round": round_name,
                "venue": venue,
                "season": SEASON,

                "K": to_int(cols[1].text),
                "HB": to_int(cols[2].text),
                "D": to_int(cols[3].text),
                "M": to_int(cols[4].text),
                "G": to_int(cols[5].text),
                "B": to_int(cols[6].text),
                "T": to_int(cols[7].text),
                "HO": to_int(cols[8].text),
                "GA": to_int(cols[9].text),
                "I50": to_int(cols[10].text),
                "CL": to_int(cols[11].text),
                "CG": to_int(cols[12].text),
                "R50": to_int(cols[13].text),
                "FF": to_int(cols[14].text),
                "FA": to_int(cols[15].text),
                "AF": to_int(cols[16].text),
                "SC": to_int(cols[17].text)
            }

            data.append(entry)

        print(f"Players parsed (team {team_index+1}):", len(valid_rows))

        team_index += 1

        if team_index > 1:
            break

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
