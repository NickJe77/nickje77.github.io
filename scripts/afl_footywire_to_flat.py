import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("AFL FOOTYWIRE → FIXED SCRAPER")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path(f"docs/data/afl/afl_{YEAR}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -------------------------------
# HELPERS
# -------------------------------
def clean(x):
    return x.strip() if x else ""


def num(x):
    try:
        return int(x)
    except:
        return 0


# -------------------------------
# GET MATCH LINKS
# -------------------------------
def get_matches():
    url = f"{BASE}ft_match_list?year={YEAR}"

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        if "ft_match_statistics?mid=" in a["href"]:
            full = BASE + a["href"]
            if full not in links:
                links.append(full)

    print("Matches found:", len(links))
    return links


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(url, idx):
    print("Scraping:", url)

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    rows = []

    # -------------------------------
    # TEAM NAMES
    # -------------------------------
    team_headers = soup.find_all("h2")

    if len(team_headers) < 2:
        print("No team headers")
        return []

    team1 = clean(team_headers[0].text)
    team2 = clean(team_headers[1].text)

    # -------------------------------
    # FIND PLAYER TABLES ONLY
    # -------------------------------
    tables = soup.find_all("table")
    player_tables = []

    for t in tables:
        headers = [clean(th.text) for th in t.find_all("th")]

        if "Player" in headers and "D" in headers:
            player_tables.append(t)

    if len(player_tables) < 2:
        print("No valid player tables")
        return []

    # -------------------------------
    # EXTRACT PLAYERS
    # -------------------------------
    def extract(table, team, opp):
        out = []

        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")

            if len(tds) < 5:
                continue

            name = clean(tds[0].text)

            # Skip junk rows
            if name == "" or "AFL" in name or "Statistics" in name:
                continue

            d = num(tds[3].text)
            g = num(tds[6].text) if len(tds) > 6 else 0
            b = num(tds[7].text) if len(tds) > 7 else 0

            out.append({
                "match_id": match_id,
                "season": YEAR,
                "round": "",
                "player": name,
                "played_for": team,
                "played_against": opp,
                "D": d,
                "G": g,
                "B": b,
                "date_iso": "",
                "venue": "",
                "crowd": ""
            })

        return out

    rows.extend(extract(player_tables[0], team1, team2))
    rows.extend(extract(player_tables[1], team2, team1))

    return rows


# -------------------------------
# MAIN
# -------------------------------
def main():
    links = get_matches()

    all_rows = []

    for i, link in enumerate(links, start=1):
        try:
            rows = parse_match(link, i)
            all_rows.extend(rows)
        except Exception as e:
            print("Error:", e)

        time.sleep(1)

    print("TOTAL PLAYER ROWS:", len(all_rows))

    with open(OUTPUT, "w") as f:
        json.dump(all_rows, f, indent=2)

    print("DONE →", OUTPUT)


if __name__ == "__main__":
    main()
