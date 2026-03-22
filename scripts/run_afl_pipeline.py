import json
import re
import time
from pathlib import Path
from collections import defaultdict

import cloudscraper
from bs4 import BeautifulSoup

print("AFL PIPELINE (CLOUDSCRAPER VERSION)")

BASE = "https://www.footywire.com"
SEASON = 2026

DATA_DIR = Path("docs/data/afl")
OUTPUT = DATA_DIR / f"afl_{SEASON}.json"
PLAYERS_DIR = DATA_DIR / "players"
PLAYERS_JSON = DATA_DIR / "players.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)


# 🔥 REAL BROWSER SESSION
scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    }
)


# -------------------------------
# HELPERS
# -------------------------------
def clean(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def to_int(text):
    try:
        return int(clean(text))
    except:
        return 0


# -------------------------------
# FETCH (BYPASS BLOCK)
# -------------------------------
def fetch(url):
    for i in range(5):
        try:
            res = scraper.get(url, timeout=30)

            if res.status_code == 200 and len(res.text) > 5000:
                return res.text

        except Exception as e:
            print("fetch error:", e)

        time.sleep(3)

    print("FAILED:", url)
    return None


# -------------------------------
# ROUND DETECTION
# -------------------------------
def get_round_label(soup):
    text = soup.get_text(" ", strip=True).lower()

    if "grand final" in text: return "Grand Final"
    if "preliminary final" in text: return "Preliminary Final"
    if "semi final" in text: return "Semi Final"
    if "qualifying final" in text: return "Qualifying Final"
    if "elimination final" in text: return "Elimination Final"

    m = re.search(r"round\s+(\d+)", text)
    if m:
        return f"Round {int(m.group(1))}"

    return None


# -------------------------------
# GET LINKS
# -------------------------------
def get_links():
    links = set()

    for rnd in range(0, 31):
        url = f"{BASE}/afl/footy/ft_match_list?year={SEASON}&round={rnd}"

        print("Round:", rnd)

        html = fetch(url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "ft_match_statistics" not in href:
                continue

            if href.startswith("/"):
                href = BASE + href
            elif not href.startswith("http"):
                href = BASE + "/afl/footy/" + href

            links.add(href)

        time.sleep(2)

    print("MATCH LINKS:", len(links))
    return sorted(links)


# -------------------------------
# PARSE MATCH
# -------------------------------
def parse_match(url, match_counter):
    html = fetch(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("title")
    if not title:
        return []

    text = clean(title.text.replace("AFL Match Statistics :", ""))

    if " def " not in text:
        return []

    team_a, team_b = text.split(" def ", 1)
    team_b = team_b.split(" at ")[0]

    round_label = get_round_label(soup)
    if not round_label:
        round_label = f"Round {match_counter}"

    match_id = f"{SEASON}_{match_counter:04d}"

    rows = soup.find_all("tr")

    current_team = None
    data = []

    for tr in rows:
        txt = clean(tr.get_text(" ", strip=True))

        m = re.match(r"^(.*?) Match Statistics", txt)
        if m:
            current_team = clean(m.group(1))
            continue

        if not current_team:
            continue

        cols = tr.find_all("td", recursive=False)
        if len(cols) < 18:
            continue

        link = cols[0].find("a")
        if not link:
            continue

        name = clean(link.text)
        opponent = team_b if current_team == team_a else team_a

        row = {
            "match_id": match_id,
            "player": name,
            "played_for": current_team,
            "played_against": opponent,
            "season": SEASON,
            "round": round_label,
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
            "SC": to_int(cols[17].text),
        }

        data.append(row)

    print(f"Match {match_counter}: {len(data)} rows")
    return data


# -------------------------------
# SCRAPE
# -------------------------------
def scrape():
    all_rows = []
    match_counter = 0

    links = get_links()

    for link in links:
        match_counter += 1

        print("Match:", match_counter)

        time.sleep(3)

        rows = parse_match(link, match_counter)
        all_rows.extend(rows)

    print("TOTAL ROWS:", len(all_rows))
    return all_rows


# -------------------------------
# BUILD PLAYERS
# -------------------------------
def build_players(rows):
    players = {}

    for r in rows:
        name = r.get("player")
        if not name:
            continue

        if name not in players:
            players[name] = {
                "name": name,
                "games": [],
                "career": defaultdict(int),
            }

        players[name]["games"].append(r)

        for k, v in r.items():
            if isinstance(v, (int, float)):
                players[name]["career"][k] += v

    return players


def save_players(players):
    summary = []

    for name, p in players.items():
        slug = name.lower().replace(" ", "-")

        (PLAYERS_DIR / f"{slug}.json").write_text(json.dumps({
            "name": name,
            "career": dict(p["career"]),
            "games": p["games"]
        }, indent=2))

        summary.append({
            "name": name,
            "slug": slug,
            "games": len(p["games"])
        })

    PLAYERS_JSON.write_text(json.dumps(summary, indent=2))


# -------------------------------
# MAIN
# -------------------------------
def main():
    rows = scrape()

    if len(rows) < 1000:
        print("❌ STILL BLOCKED")
        return

    OUTPUT.write_text(json.dumps(rows, indent=2))
    print("✅ MATCH DATA SAVED")

    players = build_players(rows)
    save_players(players)

    print("✅ PLAYERS BUILT")


if __name__ == "__main__":
    main()
