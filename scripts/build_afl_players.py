import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

print("AFL SCRAPER — FINAL (WRITE GUARANTEED)")

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

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        if "ft_match_statistics" in a["href"]:
            links.append(BASE + a["href"])

    links = list(set(links))

    print("Matches found:", len(links))
    return links


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→", url)

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("title").text

    # 🔥 FIXED TEAM PARSING
    if " def " in title:
        parts = title.split(" def ")
    elif " defeats " in title:
        parts = title.split(" defeats ")
    else:
        print("⚠️ Could not parse teams:", title)
        return []

    team1 = parts[0].replace("AFL Match Statistics :", "").strip()
    team2 = parts[1].split(" at ")[0].strip()

    tables = soup.find_all("table")

    player_tables = []

    for t in tables:
        text = t.get_text(" ", strip=True)
        if "K" in text and "HB" in text and "D" in text and "G" in text:
            player_tables.append(t)

    if len(player_tables) < 2:
        print("⚠️ Not enough tables")
        return []

    data = []

    teams = [team1, team2]

    for i in range(2):

        table = player_tables[i]
        rows = table.find_all("tr")

        count = 0

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 10:
                continue

            name = cols[0].text.strip()

            if not name or name == "Player":
                continue

            entry = {
                "player": name,
                "played_for": teams[i],
                "played_against": teams[1 - i],
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
            count += 1

        print(f"{teams[i]} players:", count)

    return data


# -----------------------------
# RUN
# -----------------------------
links = get_links()

all_data = []

for link in links:
    try:
        match_data = parse_match(link)
        all_data.extend(match_data)
    except Exception as e:
        print("ERROR:", e)


print("TOTAL PLAYER ROWS:", len(all_data))

# 🔥 GUARANTEED WRITE
with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("✅ FILE WRITTEN:", OUTPUT)
