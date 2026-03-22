import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

print("AFL SCRAPER — FINAL COMPLETE FIX (CORRECT TEAMS + ROUND)")

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


def norm_space(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


# -----------------------------
# GET MATCH LINKS
# -----------------------------
def get_links():
    links = set()

    for rnd in range(0, 31):  # includes Opening Round as round 0
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"
        print(f"Checking Round {rnd}...")

        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
        except Exception as e:
            print("Request failed:", e)
            continue

        if res.status_code != 200:
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        found = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "ft_match_statistics" not in href:
                continue

            if href.startswith("/"):
                href = BASE + href
            elif not href.startswith("http"):
                href = BASE + "/afl/footy/" + href

            links.add(href)
            found += 1

        print(f"  → Found {found} matches")

    links = sorted(links)
    print("TOTAL MATCHES FOUND:", len(links))

    if not links:
        raise Exception("❌ NO MATCH LINKS FOUND")

    return links


# -----------------------------
# PARSE TITLE TEAMS
# -----------------------------
def parse_title_teams(title):
    clean_title = title.replace("AFL Match Statistics :", "").strip()

    if " def " in clean_title:
        parts = clean_title.split(" def ")
        winner = norm_space(parts[0])
        loser = norm_space(parts[1].split(" at ")[0])
        return winner, loser

    if " defeats " in clean_title:
        parts = clean_title.split(" defeats ")
        winner = norm_space(parts[0])
        loser = norm_space(parts[1].split(" at ")[0])
        return winner, loser

    if " defeated by " in clean_title:
        parts = clean_title.split(" defeated by ")
        loser = norm_space(parts[0])
        winner = norm_space(parts[1].split(" at ")[0])
        return winner, loser

    return None, None


# -----------------------------
# FIND ROUND
# -----------------------------
def extract_round(soup):
    for tag in soup.find_all(["td", "b", "span", "div"]):
        txt = norm_space(tag.get_text(" ", strip=True))
        if "Round" in txt:
            m = re.search(r"Round\s+(\d+)", txt, re.IGNORECASE)
            if m:
                return int(m.group(1))
    return None


# -----------------------------
# FIND PLAYER TABLES + TEAM NAMES
# -----------------------------
def find_player_tables_with_teams(soup, winner, loser):
    results = []

    all_tables = soup.find_all("table")

    for table in all_tables:
        txt = norm_space(table.get_text(" ", strip=True))

        if not ("K" in txt and "HB" in txt and "D" in txt):
            continue

        team_name = None

        # Try previous elements near the table for team heading
        prev = table
        for _ in range(12):
            prev = prev.find_previous(["b", "strong", "td", "th", "div", "span"])
            if not prev:
                break

            prev_txt = norm_space(prev.get_text(" ", strip=True))
            if not prev_txt:
                continue

            if winner and winner.lower() in prev_txt.lower():
                team_name = winner
                break

            if loser and loser.lower() in prev_txt.lower():
                team_name = loser
                break

        results.append((table, team_name))

    # If exactly 2 tables and one/both team names missing, assign safely
    if len(results) >= 2:
        # only keep first two stat tables
        results = results[:2]

        names = [r[1] for r in results]

        if names[0] is None and names[1] is not None:
            results[0] = (results[0][0], winner if results[1][1] == loser else loser)

        if names[1] is None and results[0][1] is not None:
            results[1] = (results[1][0], winner if results[0][1] == loser else loser)

        if results[0][1] is None and results[1][1] is None:
            # fall back to title order only if neither table can be identified
            results[0] = (results[0][0], winner)
            results[1] = (results[1][0], loser)

    return results


# -----------------------------
# PARSE MATCH
# -----------------------------
def parse_match(url):
    print("→", url)

    res = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.find("title")
    if not title_tag:
        print("⚠️ No title found")
        return []

    title = norm_space(title_tag.text)

    round_num = extract_round(soup)
    print("ROUND FOUND:", round_num)

    winner, loser = parse_title_teams(title)
    if not winner or not loser:
        print("⚠️ Cannot parse teams from title:", title)
        return []

    player_tables = find_player_tables_with_teams(soup, winner, loser)

    if len(player_tables) < 2:
        print("⚠️ Missing player tables")
        return []

    data = []

    for table, played_for in player_tables[:2]:
        if not played_for:
            print("⚠️ Could not identify team for player table")
            continue

        played_against = loser if played_for == winner else winner

        rows = table.find_all("tr")
        count = 0

        for r in rows:
            cols = r.find_all("td")

            if len(cols) < 18:
                continue

            link = cols[0].find("a")
            if not link:
                continue

            name = norm_space(link.text)
            if not name:
                continue

            entry = {
                "player": name,
                "played_for": played_for,
                "played_against": played_against,
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

        print(f"{played_for} players:", count)

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

print("TOTAL PLAYER ROWS:", len(all_data))

with open(OUTPUT, "w") as f:
    json.dump(all_data, f, indent=2)

print("✅ FILE WRITTEN:", OUTPUT)
