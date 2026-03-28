import json
import time
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# =========================
# PATHS
# =========================

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
MATCHES_DIR = BASE_DIR / "matches"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)
MATCHES_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# CONFIG
# =========================

HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.utcnow().year
YEARS = [2025, CURRENT_YEAR]

URLS = {
    "M": lambda y: f"https://www.tennisexplorer.com/results/?type=ATP&year={y}",
    "F": lambda y: f"https://www.tennisexplorer.com/results/?type=WTA&year={y}",
}

# =========================
# UTIL FUNCTIONS
# =========================

def get(url):
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def slug(text):
    return (
        text.lower()
        .replace(".", "")
        .replace(",", "")
        .replace("'", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "-")
    )


def is_player_row(row):
    links = row.find_all("a")
    if not links:
        return False

    name = links[0].get_text(strip=True)

    # must look like tennis player
    if len(name.split()) < 2:
        return False

    if "." not in name:
        return False

    return True


def is_junk_event(name):
    name = (name or "").lower()

    return any(x in name for x in [
        "futures",
        "itf",
        "challenger",
        "utr",
        "exhibition",
        "junior"
    ])


def parse_score(cols1, cols2):
    score = []

    for i in range(3, min(len(cols1), len(cols2))):
        a = cols1[i].get_text(strip=True)
        b = cols2[i].get_text(strip=True)

        if a.isdigit() and b.isdigit():
            score.append(f"{a}-{b}")

    return " ".join(score)


def extract_date(cols, year):
    try:
        raw = cols[0].get_text(strip=True)
        if "." in raw:
            d, m = raw.split(".")[:2]
            return f"{year}{int(m):02d}{int(d):02d}"
    except:
        pass

    return f"{year}0101"


# =========================
# PARSER
# =========================

def parse_page(url, gender, year):
    print(f"Scraping {url}")

    html = get(url)
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tr")

    matches = []
    current_tournament = ""

    i = 0
    while i < len(rows) - 1:
        r1 = rows[i]
        r2 = rows[i + 1]

        # detect tournament header
        header_text = r1.get_text(" ", strip=True)

        if header_text and len(header_text) < 40 and "." not in header_text and ":" not in header_text:
            if any(c.isalpha() for c in header_text):
                current_tournament = header_text

        # skip if junk event
        if is_junk_event(current_tournament):
            i += 1
            continue

        # must be player rows
        if not is_player_row(r1) or not is_player_row(r2):
            i += 1
            continue

        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        if not cols1 or not cols2:
            i += 1
            continue

        links1 = r1.find_all("a")
        links2 = r2.find_all("a")

        if not links1 or not links2:
            i += 1
            continue

        p1 = links1[0].get_text(strip=True)
        p2 = links2[0].get_text(strip=True)

        if not p1 or not p2 or p1 == p2:
            i += 1
            continue

        date = extract_date(cols1, year)
        score = parse_score(cols1, cols2)

        match = {
            "match_id": f"{date}_{slug(p1)}_vs_{slug(p2)}",
            "tournament": current_tournament,
            "surface": "",
            "round": "",
            "player1": p1,
            "player2": p2,
            "score": score,
            "date": date,
            "gender": gender,
        }

        matches.append(match)
        i += 2

    print(f"✔ {len(matches)} matches parsed")
    return matches


# =========================
# MERGE / DEDUPE
# =========================

def load_existing(path):
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
    except:
        pass

    return []


def dedupe(matches):
    seen = set()
    clean = []

    for m in matches:
        key = (m["date"], m["player1"], m["player2"], m["score"])

        if key in seen:
            continue

        seen.add(key)
        clean.append(m)

    return clean


# =========================
# SAVE
# =========================

def save_outputs(year, new_matches):
    season_file = SEASONS_DIR / f"{year}.json"
    matches_file = MATCHES_DIR / f"{year}.json"

    existing = load_existing(matches_file)

    combined = existing + new_matches
    combined = dedupe(combined)

    matches_file.write_text(json.dumps(combined, indent=2))
    season_file.write_text(json.dumps(combined, indent=2))

    print(f"Saved {year}: {len(combined)} matches")


# =========================
# MAIN
# =========================

def main():
    print("=== TENNIS SCRAPER START ===")

    for year in YEARS:
        all_matches = []

        for gender in ["M", "F"]:
            try:
                url = URLS[gender](year)
                matches = parse_page(url, gender, year)
                all_matches.extend(matches)
                time.sleep(2)
            except Exception as e:
                print(f"ERROR {year} {gender}: {e}")

        save_outputs(year, all_matches)

    print("=== DONE ===")


if __name__ == "__main__":
    main()
