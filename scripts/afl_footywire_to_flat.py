import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL SCRAPER — ROW-BASED TEAM PARSER")

BASE = "https://www.footywire.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
SEASON = 2026

OUTPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def to_int(text):
    text = clean(text)
    try:
        return int(text)
    except:
        return 0


# -------------------------------
# ROUND FORMAT (FIX)
# -------------------------------
def format_round(r):
    if r is None:
        return None
    return f"Round {r}"


# -------------------------------
# GET LINKS
# -------------------------------
def get_links():
    links = set()

    for rnd in range(0, 31):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"
        print(f"Checking round {rnd}...")

        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            res.raise_for_status()
        except Exception as e:
            print("  request failed:", e)
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

    links = sorted(links)
    print("TOTAL MATCH LINKS:", len(links))
    return links


def get_round(soup):
    page_text = clean(soup.get_text(" ", strip=True))
    m = re.search(r"Round\s+(\d+)", page_text)
    return int(m.group(1)) if m else None


def parse_title_teams(title_text):
    title_text = clean(title_text.replace("AFL Match Statistics :", ""))

    if " def " in title_text:
        a, b = title_text.split(" def ", 1)
        return clean(a), clean(b.split(" at ")[0])

    if " defeats " in title_text:
        a, b = title_text.split(" defeats ", 1)
        return clean(a), clean(b.split(" at ")[0])

    if " defeated by " in title_text:
        loser, winner_part = title_text.split(" defeated by ", 1)
        return clean(winner_part.split(" at ")[0]), clean(loser)

    return None, None


# -------------------------------
# PARSE MATCH (FIXED)
# -------------------------------
def parse_match(url, match_counter):
    print("→", url)

    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        res.raise_for_status()
    except Exception as e:
        print("  failed to fetch match:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.find("title")
    if not title_tag:
        return []

    team_a, team_b = parse_title_teams(title_tag.get_text(" ", strip=True))
    if not team_a or not team_b:
        return []

    round_num = get_round(soup)

    # 🔥 MATCH ID FIX (THIS IS THE KEY)
    match_id = f"{SEASON}_R{round_num:02d}_{match_counter:03d}"

    rows = soup.find_all("tr")
    current_team = None
    data = []

    for tr in rows:
        row_text = clean(tr.get_text(" ", strip=True))

        m = re.match(r"^(.*?) Match Statistics \(Sorted by Disposals\)", row_text)
        if m:
            header_team = clean(m.group(1))
            if header_team == team_a or header_team == team_b:
                current_team = header_team
            else:
                current_team = None
            continue

        if not current_team:
            continue

        cols = tr.find_all("td", recursive=False)
        if len(cols) < 18:
            continue

        link = cols[0].find("a", href=True)
        if not link:
            continue

        player_name = clean(link.get_text(" ", strip=True))
        if not player_name:
            continue

        opponent = team_b if current_team == team_a else team_a

        entry = {
            "match_id": match_id,                     # ✅ FIX
            "player": player_name,
            "played_for": current_team,
            "played_against": opponent,
            "season": SEASON,
            "round": format_round(round_num),         # ✅ FIX
            "K": to_int(cols[1].get_text()),
            "HB": to_int(cols[2].get_text()),
            "D": to_int(cols[3].get_text()),
            "M": to_int(cols[4].get_text()),
            "G": to_int(cols[5].get_text()),
            "B": to_int(cols[6].get_text()),
            "T": to_int(cols[7].get_text()),
            "HO": to_int(cols[8].get_text()),
            "GA": to_int(cols[9].get_text()),
            "I50": to_int(cols[10].get_text()),
            "CL": to_int(cols[11].get_text()),
            "CG": to_int(cols[12].get_text()),
            "R50": to_int(cols[13].get_text()),
            "FF": to_int(cols[14].get_text()),
            "FA": to_int(cols[15].get_text()),
            "AF": to_int(cols[16].get_text()),
            "SC": to_int(cols[17].get_text()),
        }

        data.append(entry)

    print("  parsed rows:", len(data))
    return data


# -------------------------------
# MAIN
# -------------------------------
all_data = []
match_counter = 0

for link in get_links():
    match_counter += 1
    match_rows = parse_match(link, match_counter)
    all_data.extend(match_rows)

print("TOTAL PLAYER ROWS:", len(all_data))

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print("WRITTEN:", OUTPUT)
