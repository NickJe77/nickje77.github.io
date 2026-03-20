import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re
from datetime import datetime

print("AFL FOOTYWIRE → FINAL PRODUCTION (FIXED)")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON_OUTPUT = Path(f"docs/data/afl/afl_{YEAR}.json")
PLAYERS_OUTPUT = Path("docs/data/afl/players.json")

SEASON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)


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


def format_score(points):
    goals = points // 6
    behinds = points % 6
    return f"{goals}.{behinds} ({points})"


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
# PARSE HEADER
# -------------------------------
def parse_header(soup):

    text = soup.get_text("\n")

    team1 = ""
    team2 = ""
    round_name = ""
    venue = ""
    crowd = ""
    date_iso = ""
    home_score = 0
    away_score = 0

    for line in text.split("\n"):

        # ---------------- TEAM RESULT ----------------
        if "defeats" in line:
            parts = line.split("defeats")
            if len(parts) == 2:
                team1 = clean(parts[0])
                team2 = clean(parts[1])

        if " drew " in line:
            parts = line.split("drew")
            if len(parts) == 2:
                team1 = clean(parts[0])
                team2 = clean(parts[1])

        # ---------------- ROUND ----------------
        round_match = re.search(r"(Round\s+\d+)", line)
        if round_match:
            round_name = round_match.group(1)

        # ---------------- VENUE + CROWD ----------------
        if "Attendance" in line:
            parts = line.split(",")
            if len(parts) >= 2:
                venue = parts[1].strip()

            crowd_match = re.search(r"(\d+)", line)
            if crowd_match:
                crowd = crowd_match.group(1)

        # ---------------- DATE ----------------
        if "2026" in line and ":" in line:
            try:
                dt = datetime.strptime(line.strip(), "%A, %d %B %Y, %I:%M %p AEDT")
                date_iso = dt.isoformat()
            except:
                pass

    # ---------------- SCORE TABLE ----------------
    score_table = soup.find("table")

    if score_table:
        rows = score_table.find_all("tr")

        if len(rows) >= 3:
            try:
                home_score = int(rows[1].find_all("td")[-1].text)
                away_score = int(rows[2].find_all("td")[-1].text)
            except:
                pass

    return (
        team1, team2,
        round_name, venue, crowd, date_iso,
        home_score, away_score
    )


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(url, idx):
    print("Scraping:", url)

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    (
        team1, team2,
        round_name, venue, crowd, date_iso,
        home_score, away_score
    ) = parse_header(soup)

    # 🚨 Skip bad matches
    if team1 == "" or team2 == "":
        return []

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

                # FULL STATS
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
                "crowd": crowd,

                # ✅ NEW
                "team_score": home_score if team == team1 else away_score,
                "opp_score": away_score if team == team1 else home_score,
                "team_score_str": format_score(home_score if team == team1 else away_score),
                "opp_score_str": format_score(away_score if team == team1 else home_score),
            })

        return rows

    data = []
    data.extend(extract(player_tables[0], team1, team2))
    data.extend(extract(player_tables[1], team2, team1))

    return data


# -------------------------------
# BUILD PLAYERS
# -------------------------------
def build_players(all_rows):

    players = {}

    for r in all_rows:
        name = r["player"]

        if name not in players:
            players[name] = {
                "player": name,
                "games": 0,
                "K": 0, "HB": 0, "D": 0, "M": 0,
                "G": 0, "B": 0, "T": 0
            }

        p = players[name]

        p["games"] += 1
        p["K"] += r["K"]
        p["HB"] += r["HB"]
        p["D"] += r["D"]
        p["M"] += r["M"]
        p["G"] += r["G"]
        p["B"] += r["B"]
        p["T"] += r["T"]

    return list(players.values())


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

    # SAVE SEASON
    with open(SEASON_OUTPUT, "w") as f:
        json.dump(all_rows, f, indent=2)

    # SAVE PLAYERS
    players = build_players(all_rows)

    with open(PLAYERS_OUTPUT, "w") as f:
        json.dump(players, f, indent=2)

    print("DONE — FULL AFL PIPELINE COMPLETE")


if __name__ == "__main__":
    main()
