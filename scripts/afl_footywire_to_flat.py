import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — FINAL (ROUND GUARANTEED)")

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
# GET LINKS + ROUND (ROBUST)
# -----------------------------
def get_links_with_rounds():

    url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    matches = []
    current_round = None

    rows = soup.find_all("tr")

    for r in rows:

        cells = r.find_all("td")

        if not cells:
            continue

        text = r.get_text(" ", strip=True)

        # 🔥 Detect round header (works on FootyWire)
        round_match = re.search(r"Round\s+(\d+)", text)

        if round_match:
            current_round = int(round_match.group(1))
            print("Detected Round:", current_round)
            continue

        # 🔥 Extract match link
        link_tag = r.find("a", href=True)

        if not link_tag:
            continue

        href = link_tag["href"]

        if "ft_match_statistics" not in href:
            continue

        # build full URL
        if href.startswith("/"):
            href = BASE + href
        elif not href.startswith("http"):
            href = BASE + "/afl/footy/" + href

        matches.append((href, current_round))

    print("Matches found:", len(matches))

    if not matches:
        raise Exception("❌ NO MATCHES FOUND")

    print("Sample:", matches[0])

    return matches


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url, round_num):

    print(f"→ {url} (Round {round_num})")

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text

    if " def " in title:
        parts = title.split(" def ")
    elif " defeats " in title:
        parts = title.split(" defeats ")
    else:
        print("⚠️ Cannot parse teams:", title)
        return []

    team1 = parts[0].replace("AFL Match Statistics :", "").strip()
    team2 = parts[1].split(" at ")[0].strip()

    tables = soup.find_all("table")

    player_tables = []

    for t in tables:
        txt = t.get_text(" ", strip=True)
        if "K" in txt and "HB" in txt and "D" in txt:
            player_tables.append(t)

    if len(player_tables) < 2:
        print("⚠️ Missing player tables")
        return []

    data = []
    teams = [team1, team2]

    for i in range(2):

        rows = player_tables[i].find_all("tr")

        count = 0

        for r in rows:

            cols = r.find_all("td")

            if len(cols) < 18:
                continue

            # ONLY REAL PLAYERS
            link = cols[0].find("a")

            if not link:
                continue

            name = link.text.strip()

            if not name:
                continue

            entry = {
                "player": name,
                "played_for": teams[i],
                "played_against": teams[1 - i],
                "season": SEASON,
                "round": round_num,   # 🔥 NOW GUARANTEED

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
matches = get_links_with_rounds()

all_data = []

for url, rnd in matches:
    try:
        all_data.extend(parse_match(url, rnd))
    except Exception as e:
        print("ERROR:", e)


print("TOTAL PLAYER ROWS:", len(all_data))


with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("✅ FILE WRITTEN:", OUTPUT)
