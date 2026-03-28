import json
import time
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# -------------------------
# PATHS
# -------------------------

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
MATCHES_DIR = BASE_DIR / "matches"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)
MATCHES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# CONFIG
# -------------------------

HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.utcnow().year
YEARS = [2025, CURRENT_YEAR]

URLS = {
    "M": lambda y: f"https://www.tennisexplorer.com/results/?type=ATP&year={y}",
    "F": lambda y: f"https://www.tennisexplorer.com/results/?type=WTA&year={y}",
}

# -------------------------
# HELPERS
# -------------------------

def get(url):
    return SESSION.get(url, timeout=30).text


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


# 🔥 STRICT FILTER (NO FALLBACK)
def is_main_tour_event(name):
    name = (name or "").lower().strip()

    # ❌ HARD EXCLUDE
    if any(x in name for x in [
        "futures",
        "itf",
        "challenger",
        "utr",
        "exhibition",
        "junior",
        "qualification"
    ]):
        return False

    # ✅ GRAND SLAMS
    if any(x in name for x in [
        "australian open",
        "french open",
        "wimbledon",
        "us open"
    ]):
        return True

    # ✅ ATP/WTA TOUR KEYWORDS
    if any(x in name for x in [
        "masters",
        "atp",
        "wta",
        "finals",
        "1000",
        "500",
        "250"
    ]):
        return True

    # ✅ KNOWN TOUR EVENTS (covers most)
    allowed = [
        "miami",
        "madrid",
        "rome",
        "indian wells",
        "toronto",
        "cincinnati",
        "shanghai",
        "paris",
        "rotterdam",
        "dubai",
        "doha",
        "acapulco",
        "monte carlo",
        "barcelona",
        "hamburg",
        "vienna",
        "basel",
        "tokyo",
        "beijing",
        "washington",
        "halle",
        "queen",
        "adelaide",
        "brisbane",
        "sydney",
        "auckland"
    ]

    if any(x in name for x in allowed):
        return True

    return False


def parse_score(cols1, cols2):
    score_parts = []

    for i in range(3, min(len(cols1), len(cols2))):
        a = cols1[i].get_text(strip=True)
        b = cols2[i].get_text(strip=True)

        if a.isdigit() and b.isdigit():
            score_parts.append(f"{a}-{b}")

    return " ".join(score_parts)


def is_player_row(row):
    links = row.find_all("a")
    if not links:
        return False

    name = links[0].get_text(strip=True)

    if len(name.split()) < 2:
        return False

    if "." not in name:
        return False

    return True


# -------------------------
# PARSER
# -------------------------

def parse_page(url, gender, year):
    print(f"Scraping {url}")

    soup = BeautifulSoup(get(url), "html.parser")
    rows = soup.select("table tr")

    matches = []
    current_tournament = ""

    i = 0
    while i < len(rows) - 1:
        r1 = rows[i]
        r2 = rows[i + 1]

        # detect tournament header
        text = r1.get_text(" ", strip=True)

        if text and len(text) < 40 and "." not in text and ":" not in text:
            if any(c.isalpha() for c in text):
                if is_main_tour_event(text):
                    current_tournament = text
                else:
                    current_tournament = ""

        # must be player rows
        if not is_player_row(r1) or not is_player_row(r2):
            i += 1
            continue

        # skip invalid tournaments
        if not current_tournament:
            i += 2
            continue

        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        p1 = r1.find_all("a")[0].get_text(strip=True)
        p2 = r2.find_all("a")[0].get_text(strip=True)

        if p1 == p2:
            i += 1
            continue

        # date
        date = f"{year}0101"
        try:
            raw = cols1[0].get_text(strip=True)
            if "." in raw:
                d, m = raw.split(".")[:2]
                date = f"{year}{int(m):02d}{int(d):02d}"
        except:
            pass

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


# -------------------------
# MERGE / DEDUPE
# -------------------------

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


# -------------------------
# SAVE
# -------------------------

def save_outputs(year, new_matches):
    season_path = SEASONS_DIR / f"{year}.json"
    matches_path = MATCHES_DIR / f"{year}.json"

    existing = load_existing(matches_path)

    combined = existing + new_matches
    combined = dedupe(combined)

    matches_path.write_text(json.dumps(combined, indent=2))
    season_path.write_text(json.dumps(combined, indent=2))

    print(f"Saved {year} → {len(combined)} matches")


# -------------------------
# MAIN
# -------------------------

def main():
    print("RUNNING TENNIS SCRAPER (STRICT FILTER FINAL)")

    for year in YEARS:
        year_matches = []

        for gender in ["M", "F"]:
            try:
                url = URLS[gender](year)
                data = parse_page(url, gender, year)
                year_matches.extend(data)
                time.sleep(2)
            except Exception as e:
                print(f"FAIL {year} {gender}: {e}")

        save_outputs(year, year_matches)

    print("DONE")


if __name__ == "__main__":
    main()
