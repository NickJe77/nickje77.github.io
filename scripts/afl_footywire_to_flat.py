import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("AFL FOOTYWIRE → FINAL CLEAN SCRAPER")

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
    # TEAM NAMES (FROM HEADER TEXT)
    # -------------------------------
    page_text = soup.get_text(separator="\n")

    team1 = "Team 1"
    team2 = "Team 2"

    for line in page_text.split("\n"):
        if "defeats" in line:
            parts = line.split("defeats")
            if len(parts) == 2:
                team1 = clean(parts[0])
                team2 = clean(parts[1])
            break

    # fallback (rare)
    if team1 == "Team 1":
        title = soup.title.text if soup.title else ""
        if " vs " in title:
            parts = title.split(" vs ")
            team1 = clean(parts[0].replace("AFL Statistics", ""))
            team2 = clean(parts[1].split("|")[0])

    # -------------------------------
    # FIND PLAYER TABLES
    # -------------------------------
    tables = soup.find_all("table")

    player_tables = [t for t in tables if len(t.find_all("tr")) > 25]

    if len(player_tables) < 2:
        return []

    # -------------------------------
    # EXTRACT PLAYERS
    # -------------------------------
    def extract(table, team, opp):
        out = []

        for tr in table.find_all("tr"):
            tds = tr.find_all("td")

            if len(tds) < 8:
                continue

            name = clean(tds[0].text)

            # REMOVE NON-PLAYER ROWS
            if (
                name == ""
                or "AFL" in name
                or "Round" in name
                or "Attendance" in name
                or "defeats" in name
                or "Player" in name
                or "\n" in name
            ):
                continue

            if len(name.split()) < 2:
                continue

            d = num(tds[3].text)
            g = num(tds[6].text)
            b = num(tds[7].text)

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

    # 🚨 SAFETY: DO NOT WIPE FILE
    if len(all_rows) < 100:
        print("FAILED — not saving (prevents data wipe)")
        return

    with open(OUTPUT, "w") as f:
        json.dump(all_rows, f, indent=2)

    print("DONE →", OUTPUT)


if __name__ == "__main__":
    main()
