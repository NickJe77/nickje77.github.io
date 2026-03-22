import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — ROUND DEBUG VERSION")

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

    links = set()

    for rnd in range(1, 31):

        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"

        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", href=True):

            href = a["href"]

            if "ft_match_statistics" not in href:
                continue

            if href.startswith("/"):
                href = BASE + href
            elif not href.startswith("http"):
                href = BASE + "/afl/footy/" + href

            links.add(href)

    links = list(links)

    print("MATCHES FOUND:", len(links))

    if not links:
        raise Exception("NO MATCHES FOUND")

    return links


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text

    # -----------------------------
    # ROUND (STRICT)
    # -----------------------------
    round_num = None

    for tag in soup.find_all(["td", "b", "span", "div"]):
        txt = tag.get_text(" ", strip=True)

        if "Round" in txt:
            m = re.search(r"Round\s+(\d+)", txt)
            if m:
                round_num = int(m.group(1))
                break

    print("ROUND FOUND:", round_num)  # 👈 DEBUG LINE

    # -----------------------------
    # TEAMS
    # -----------------------------
    if " def " in title:
        parts = title.split(" def ")
    elif " defeats " in title:
        parts = title.split(" defeats ")
    else:
        return []

    team1 = parts[0].replace("AFL Match Statistics :", "").strip()
    team2 = parts[1].split(" at ")[0].strip()

    # -----------------------------
    # PLAYER TABLES
    # -----------------------------
    tables = soup.find_all("table")

    player_tables = []

    for t in tables:
        txt = t.get_text(" ", strip=True)
        if "K" in txt and "HB" in txt and "D" in txt:
            player_tables.append(t)

    if len(player_tables) < 2:
        return []

    data = []
    teams = [team1, team2]

    for i in range(2):

        rows = player_tables[i].find_all("tr")

        for r in rows:

            cols = r.find_all("td")

            if len(cols) < 18:
                continue

            link = cols[0].find("a")
            if not link:
                continue

            name = link.text.strip()
            if not name:
                continue

            data.append({
                "player": name,
                "played_for": teams[i],
                "played_against": teams[1 - i],
                "season": SEASON,
                "round": round_num,  # 👈 THIS MUST EXIST

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
            })

    return data


# -----------------------------
# RUN
# -----------------------------
links = get_links()

all_data = []

for link in links:
    all_data.extend(parse_match(link))

print("TOTAL ROWS:", len(all_data))

with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("DONE:", OUTPUT)
