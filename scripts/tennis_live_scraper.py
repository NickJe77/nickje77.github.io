import json
import re
import time
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.utcnow().year

# You said you care about 2025, this year, and going forward
YEARS = [year for year in range(2025, CURRENT_YEAR + 1)]

# Tennis Explorer result pages
# ATP
ATP_URLS = {
    year: f"https://www.tennisexplorer.com/results/?type=ATP&year={year}"
    for year in YEARS
}
# WTA
WTA_URLS = {
    year: f"https://www.tennisexplorer.com/results/?type=WTA&year={year}"
    for year in YEARS
}


def safe_get(url, tries=3, sleep_sec=3):
    last_err = None
    for attempt in range(1, tries + 1):
        try:
            r = SESSION.get(url, timeout=30)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            print(f"GET failed ({attempt}/{tries}) {url} -> {e}")
            time.sleep(sleep_sec)
    raise last_err


def clean_text(value):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value


def is_time_text(value):
    value = clean_text(value)
    return bool(re.fullmatch(r"\d{1,2}:\d{2}", value))


def looks_like_score(value):
    value = clean_text(value)
    if not value:
        return False

    # common tennis score patterns
    patterns = [
        r"^\d-\d(?:\(\d+\))?(?: \d-\d(?:\(\d+\))?)*$",
        r"^\d:\d(?: \d:\d)*$",
        r"^(ret\.?|walkover|w/o|wo)$",
    ]
    for p in patterns:
        if re.fullmatch(p, value.lower()):
            return True

    # loose fallback for set-like strings
    if re.search(r"\b\d[-:]\d\b", value):
        return True

    return False


def normalise_score(value):
    value = clean_text(value)
    if value.lower() in {"wo", "w/o"}:
        return "Walkover"
    return value


def looks_like_player(value):
    value = clean_text(value)
    if not value:
        return False

    bad = {
        "info", "preview", "stats", "head-to-head", "h2h",
        "commentary", "draw", "live", "result"
    }
    if value.lower() in bad:
        return False

    if is_time_text(value):
        return False

    if looks_like_score(value):
        return False

    # allow names like "Gauff C." / "Carlos Alcaraz" / "Swiatek I."
    if re.search(r"[A-Za-z]", value):
        return True

    return False


def parse_date_from_text(text, year_hint):
    text = clean_text(text)

    # Try YYYYMMDD already
    if re.fullmatch(r"\d{8}", text):
        return text

    # Try dd.mm. or dd.mm.yyyy
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if m:
        d, mth, y = m.groups()
        return f"{int(y):04d}{int(mth):02d}{int(d):02d}"

    m = re.search(r"(\d{1,2})\.(\d{1,2})\.", text)
    if m:
        d, mth = m.groups()
        return f"{int(year_hint):04d}{int(mth):02d}{int(d):02d}"

    # fallback
    return f"{int(year_hint):04d}0101"


def extract_candidate_cells(tr):
    cells = []

    for td in tr.find_all(["td", "th"]):
        txt = clean_text(td.get_text(" ", strip=True))
        if txt:
            cells.append(txt)

        # add link text separately if needed
        for a in td.find_all("a"):
            at = clean_text(a.get_text(" ", strip=True))
            if at and at not in cells:
                cells.append(at)

    return cells


def pick_players_and_score(cells):
    """
    We deliberately filter out junk like:
    - info
    - 10:10
    - preview
    Then try to identify two player names and a score.
    """
    cleaned = []
    for c in cells:
        c = clean_text(c)
        if not c:
            continue
        if c.lower() == "info":
            continue
        cleaned.append(c)

    players = []
    score = ""

    for c in cleaned:
        if not score and looks_like_score(c):
            score = normalise_score(c)
            continue

        if looks_like_player(c):
            # avoid score-like cells slipping through
            if len(players) < 2:
                players.append(c)

    if len(players) >= 2:
        return players[0], players[1], score

    return "", "", score


def detect_surface(text):
    text = clean_text(text).lower()
    for surface in ["hard", "clay", "grass", "carpet"]:
        if surface in text:
            return surface.title()
    return ""


def detect_round(text):
    text = clean_text(text)

    # ignore times masquerading as rounds
    if is_time_text(text):
        return ""

    known_rounds = [
        "Final", "Semi-final", "Semifinal", "Quarter-final", "Quarterfinal",
        "1st round", "2nd round", "3rd round", "4th round",
        "Round Robin", "Q-Final", "S-Final", "R16", "R32", "R64", "R128",
        "Q1", "Q2", "Q3"
    ]

    low = text.lower()
    for r in known_rounds:
        if r.lower() in low:
            return r

    return ""


def parse_results_page(url, gender, year):
    print(f"Fetching {url}")
    html = safe_get(url).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []

    current_tournament = ""
    current_surface = ""
    current_date = ""
    current_round = ""

    rows = soup.find_all("tr")
    print(f"Found {len(rows)} rows")

    for tr in rows:
        row_text = clean_text(tr.get_text(" ", strip=True))
        if not row_text:
            continue

        cells = extract_candidate_cells(tr)
        joined = " | ".join(cells)

        # Tournament/header style rows
        # We keep updating context when header-like rows appear
        if len(cells) <= 3:
            possible_surface = detect_surface(joined)
            possible_round = detect_round(joined)

            if possible_surface:
                current_surface = possible_surface

            if possible_round:
                current_round = possible_round

            # date rows often appear as standalone header-ish text
            if re.search(r"\d{1,2}\.\d{1,2}\.", joined) or re.search(r"\d{8}", joined):
                current_date = parse_date_from_text(joined, year)

            # tournament names are often short headers without score/player patterns
            if (
                not looks_like_score(joined)
                and not is_time_text(joined)
                and "info" not in joined.lower()
                and not re.search(r"\b\d[-:]\d\b", joined)
                and len(joined) > 3
            ):
                # avoid obvious round-only labels
                if not current_round or joined.lower() != current_round.lower():
                    # keep header if it looks like event text
                    if any(ch.isalpha() for ch in joined):
                        if not re.fullmatch(r"(hard|clay|grass|carpet)", joined.lower()):
                            current_tournament = joined

        p1, p2, score = pick_players_and_score(cells)

        # If this row is not a real result row, skip it
        if not p1 or not p2:
            continue

        # reject junk rows explicitly
        bad_values = {"info", "preview", "stats"}
        if p1.lower() in bad_values or p2.lower() in bad_values:
            continue

        if is_time_text(p1) or is_time_text(p2):
            continue

        match = {
            "tournament": current_tournament or "Unknown",
            "surface": current_surface or "",
            "round": current_round or "",
            "player1": p1,
            "player2": p2,
            "score": score or "",
            "date": current_date or f"{year}0101",
            "gender": gender,
        }

        matches.append(match)

    # dedupe
    deduped = []
    seen = set()

    for m in matches:
        key = (
            m["date"],
            m["tournament"],
            m["player1"],
            m["player2"],
            m["score"],
            m["gender"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(m)

    # final sanity filter
    final = []
    for m in deduped:
        if not m["player1"] or not m["player2"]:
            continue
        if m["player2"].lower() == "info":
            continue
        if m["score"].lower() == "info":
            continue
        if is_time_text(m["round"]):
            m["round"] = ""
        final.append(m)

    print(f"Parsed {len(final)} valid matches from {url}")
    return final


def load_existing_matches(path):
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if isinstance(data.get("matches"), list):
            return data["matches"]
        if isinstance(data.get("results"), list):
            return data["results"]

    return []


def merge_preserving_good(existing, new_matches):
    """
    Replace bad live rows with good ones, but preserve any existing rows
    that already look valid and are not duplicated.
    """
    all_rows = []

    def valid(row):
        if not isinstance(row, dict):
            return False
        p1 = clean_text(row.get("player1"))
        p2 = clean_text(row.get("player2"))
        score = clean_text(row.get("score"))
        rnd = clean_text(row.get("round"))

        if not p1 or not p2:
            return False
        if p2.lower() == "info":
            return False
        if score.lower() == "info":
            return False
        if is_time_text(rnd):
            return False
        return True

    seen = set()

    for row in existing:
        if not valid(row):
            continue
        key = (
            clean_text(row.get("date")),
            clean_text(row.get("tournament")),
            clean_text(row.get("player1")),
            clean_text(row.get("player2")),
            clean_text(row.get("score")),
            clean_text(row.get("gender")),
        )
        if key in seen:
            continue
        seen.add(key)
        all_rows.append(row)

    for row in new_matches:
        key = (
            clean_text(row.get("date")),
            clean_text(row.get("tournament")),
            clean_text(row.get("player1")),
            clean_text(row.get("player2")),
            clean_text(row.get("score")),
            clean_text(row.get("gender")),
        )
        if key in seen:
            continue
        seen.add(key)
        all_rows.append(row)

    all_rows.sort(key=lambda x: clean_text(x.get("date")))
    return all_rows


def save_year(year, matches):
    out_path = SEASONS_DIR / f"{year}.json"
    existing = load_existing_matches(out_path)
    merged = merge_preserving_good(existing, matches)
    out_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(merged)} matches -> {out_path}")


def main():
    print("TENNIS LIVE SCRAPER START")

    for year in YEARS:
        year_matches = []

        try:
            atp_matches = parse_results_page(ATP_URLS[year], "M", year)
            year_matches.extend(atp_matches)
        except Exception as e:
            print(f"ATP failed for {year}: {e}")

        time.sleep(2)

        try:
            wta_matches = parse_results_page(WTA_URLS[year], "F", year)
            year_matches.extend(wta_matches)
        except Exception as e:
            print(f"WTA failed for {year}: {e}")

        save_year(year, year_matches)
        time.sleep(2)

    print("TENNIS LIVE SCRAPER DONE")


if __name__ == "__main__":
    main()
