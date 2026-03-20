import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re
from datetime import datetime

print("AFL FOOTYWIRE → FULL PRODUCTION SCRAPER")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path(f"docs/data/afl/afl_{YEAR}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


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

    print("Matches:", len(links))
    return links


# -------------------------------
# PARSE HEADER INFO
# -------------------------------
def parse_header(soup):
    text = soup.get_text("\n")

    team1 = ""
    team2 = ""
    round_name = ""
    venue = ""
    crowd = ""
    date_iso = ""

    for line in text.split("\n"):

        # Teams
        if "defeats" in line:
            parts = line.split("defeats")
            if len(parts) == 2:
                team1 = clean(parts[0])
                team2 = clean(parts[1])

        # Round / Venue / Crowd
        if "Round" in line and "Attendance" in line:
            round_name = line.split(",")[0]
            venue = line.split(",")[1].strip()
            crowd = re.findall(r"\d+", line)
            crowd = crowd[0] if crowd else ""

        # Date
        if "2026" in line and ":" in line:
            try:
                dt = datetime.strptime(line.strip(), "%A, %d %B %Y, %I:%M %p AEDT")
                date_iso = dt.isoformat()
            except:
                pass

    return team1, team2, round_name, venue, crowd, date_iso


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(url, idx):
    print("Scraping:", url)

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    team1, team2, round_name, venue, crowd, date_iso = parse_header(soup)

    tables = soup.find_all("table")
    player_tables = [t for t in tables if len(t.find_all("tr")) > 25]

    if len(player_tables) < 2:
        return []

    def extract(table, team, opp):
        rows = []

        for tr in table.find_all("tr"):
            tds = tr.find_all("td")

            if len(tds) < 18:
                continue

            name = clean(tds[0].text)

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

            rows.append({
                "match_id": match_id,
                "season": YEAR,
                "round": round_name,
                "player": name,
                "played_for": team,
                "played_against": opp,
                "K": num(tds[1].text),
                "HB": num(tds[2].text),
                "D": num(tds[3].text),
                "M": num(tds[4].text),
                "G": num(tds[5].text),
                "B": num(tds[6].text),
                "T": num(tds[7].text),
                "HO": num(tds[8].text),
                "GA": num(tds[9].text),
                "I50": num(tds[10].text),
                "CL": num(tds[11].text),
                "CG": num(tds[12].text),
                "R50": num(tds[13].text),
                "FF": num(tds[14].text),
                "FA": num(tds[15].text),
                "AF": num(tds[16].text),
                "SC": num(tds[17].text),
                "date_iso": date_iso,
                "venue": venue,
                "crowd": crowd
            })

        return rows

    data = []
    data.extend(extract(player_tables[0], team1, team2))
    data.extend(extract(player_tables[1], team2, team1))

    return data


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

    print("TOTAL ROWS:", len(all_rows))

    if len(all_rows) < 100:
        print("FAILED — not saving")
        return

    with open(OUTPUT, "w") as f:
        json.dump(all_rows, f, indent=2)

    print("DONE")


if __name__ == "__main__":
    main()
