import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("AFL FOOTYWIRE → FLAT PLAYER JSON")

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
        try:
            return float(x)
        except:
            return 0


# -------------------------------
# GET MATCH LINKS
# -------------------------------
def get_matches():
    url = f"{BASE}ft_match_list?year={YEAR}"
    print("Fetching season:", url)

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []

    for a in soup.find_all("a", href=True):
        if "ft_match_statistics?mid=" in a["href"]:
            link = BASE + a["href"]
            if link not in matches:
                matches.append(link)

    print("Matches found:", len(matches))
    return matches


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(url, match_index):
    print("Scraping:", url)

    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")

    if len(tables) < 2:
        return []

    # Teams
    headers = soup.find_all("h2")
    team1 = clean(headers[0].text) if len(headers) > 0 else "Team A"
    team2 = clean(headers[1].text) if len(headers) > 1 else "Team B"

    # Round (rough extract)
    round_text = "Round"
    for h in soup.find_all(["h1", "h2", "h3"]):
        if "Round" in h.text:
            round_text = clean(h.text)
            break

    # Venue (best guess)
    venue = ""
    for td in soup.find_all("td"):
        if "Venue" in td.text:
            venue = clean(td.find_next("td").text)
            break

    match_id = f"{YEAR}_{str(match_index).zfill(4)}"

    rows = []

    # ---------------- TEAM TABLE PARSER ----------------
    def extract_players(table, team, opponent):
        out = []
        trs = table.find_all("tr")[1:]

        for r in trs:
            cols = r.find_all("td")

            if len(cols) < 5:
                continue

            name = clean(cols[0].text)

            d = num(cols[3].text)  # disposals
            g = num(cols[6].text) if len(cols) > 6 else 0
            b = num(cols[7].text) if len(cols) > 7 else 0

            out.append({
                "match_id": match_id,
                "season": YEAR,
                "round": round_text,
                "player": name,
                "played_for": team,
                "played_against": opponent,
                "D": d,
                "G": g,
                "B": b,
                "date_iso": "",
                "venue": venue,
                "crowd": ""
            })

        return out

    rows.extend(extract_players(tables[0], team1, team2))
    rows.extend(extract_players(tables[1], team2, team1))

    return rows


# -------------------------------
# MAIN
# -------------------------------
def main():
    links = get_matches()

    all_rows = []

    for i, link in enumerate(links, start=1):
        try:
            data = parse_match(link, i)
            all_rows.extend(data)
        except Exception as e:
            print("Error:", e)

        time.sleep(1)

    print("Total player rows:", len(all_rows))

    with open(OUTPUT, "w") as f:
        json.dump(all_rows, f, indent=2)

    print("SAVED:", OUTPUT)


if __name__ == "__main__":
    main()
