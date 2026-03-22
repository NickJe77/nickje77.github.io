import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — FINAL (ROUND FIXED PROPERLY)")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026

OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -----------------------------
# SAFE INT
# -----------------------------
def to_int(x):
    try:
        return int(x.strip())
    except:
        return 0


# -----------------------------
# EXTRACT ROUND (RELIABLE)
# -----------------------------
def extract_round(soup):

    # Look for the specific header line
    candidates = soup.find_all(["b", "td", "div", "span"])

    for tag in candidates:

        txt = tag.get_text(" ", strip=True)

        if txt.startswith("Round") and "," in txt:
            # Example: "Round 2, Adelaide Oval"
            part = txt.split(",")[0]

            try:
                return int(part.replace("Round", "").strip())
            except:
                continue

    # fallback (just in case)
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Round\s+(\d+)", text)

    if match:
        return int(match.group(1))

    return None


# -----------------------------
# GET MATCH LINKS
# -----------------------------
def get_links():

    url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}"

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    links = []

    for a in soup.select('a[href*="ft_match_statistics"]'):

        href = a.get("href", "")

        if not href:
            continue

        if href.startswith("/"):
            href = BASE + href
        elif not href.startswith("http"):
            href = BASE + "/afl/footy/" + href

        links.append(href)

    links = list(set(links))

    print("Matches found:", len(links))

    if not links:
        raise Exception("❌ NO MATCH LINKS FOUND")

    print("Sample:", links[0])

    return links


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):

    print("→", url)

    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    title = soup.find("title").text

    # -----------------------------
    # TEAM PARSING
    # -----------------------------
    if " def " in title:
        parts = title.split(" def ")
    elif " defeats " in title:
        parts = title.split(" defeats ")
    else:
        print("⚠️ Cannot parse teams:", title)
        return []

    team1 = parts[0].replace("AFL Match Statistics :", "").strip()
    team2 = parts[1].split(" at ")[0].strip()

    # -----------------------------
    # ROUND
    # -----------------------------
    round_num = extract_round(soup)
    print("ROUND:", round_num)

    # -----------------------------
    # FIND PLAYER TABLES
    # -----------------------------
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

    # -----------------------------
    # PARSE BOTH TEAMS
    # -----------------------------
    for i in range(2):

        rows = player_tables[i].find_all("tr")

        count = 0

        for r in rows:
            cols = r.find_all("td")

            if len(cols) < 18:
                continue

            # 🔥 ONLY REAL PLAYERS
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
                "round": round_num,

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
# RUN SCRAPER
# -----------------------------
links = get_links()

all_data = []

for link in links:
    try:
        all_data.extend(parse_match(link))
    except Exception as e:
        print("ERROR:", e)


print("TOTAL PLAYER ROWS:", len(all_data))


# -----------------------------
# WRITE FILE
# -----------------------------
with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("✅ FILE WRITTEN:", OUTPUT)
