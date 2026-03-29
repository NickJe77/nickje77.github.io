import csv
import io
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

START_YEAR = 1968
END_YEAR = 2024

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
MATCHES_DIR = BASE_DIR / "matches"
EVENTS_DIR = BASE_DIR / "events"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)
MATCHES_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv,application/octet-stream;q=0.9,*/*;q=0.8",
})

ATP_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv"
WTA_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_{year}.csv"


def clean_text(value) -> str:
    return str(value or "").strip()


def safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(str(value)))
    except Exception:
        return default


def parse_date(raw: str) -> str:
    raw = clean_text(raw)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def slug(text: str) -> str:
    text = clean_text(text).lower()
    out = []
    dash = False
    for ch in text:
        if ch.isalnum():
            out.append(ch)
            dash = False
        else:
            if not dash:
                out.append("-")
                dash = True
    return "".join(out).strip("-")


def normalize_round(raw: str) -> str:
    raw = clean_text(raw)
    mapping = {
        "R128": "R128",
        "R64": "R64",
        "R32": "R32",
        "R16": "R16",
        "QF": "QF",
        "SF": "SF",
        "F": "F",
        "RR": "RR",
        "BR": "Bronze Medal Match",
        "ER": "Early Round",
    }
    return mapping.get(raw, raw)


def normalize_surface(raw: str) -> str:
    raw = clean_text(raw)
    if not raw:
        return ""
    fixes = {
        "Hard": "Hard",
        "Clay": "Clay",
        "Grass": "Grass",
        "Carpet": "Carpet",
    }
    return fixes.get(raw, raw)


def normalize_score(raw: str) -> str:
    return " ".join(clean_text(raw).split())


def fetch_csv_rows(url: str) -> List[Dict[str, str]]:
    resp = SESSION.get(url, timeout=90)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def build_match_id(
    year: int,
    gender: str,
    date: str,
    tournament: str,
    rnd: str,
    winner: str,
    loser: str,
) -> str:
    return "_".join([
        str(year),
        gender.lower(),
        slug(date),
        slug(tournament),
        slug(rnd),
        slug(winner),
        slug(loser),
    ])


def row_to_match(row: Dict[str, str], gender: str) -> Optional[Dict]:
    tournament = clean_text(row.get("tourney_name"))
    winner = clean_text(row.get("winner_name"))
    loser = clean_text(row.get("loser_name"))
    if not tournament or not winner or not loser:
        return None

    date = parse_date(row.get("tourney_date"))
    rnd = normalize_round(row.get("round"))
    surface = normalize_surface(row.get("surface"))
    score = normalize_score(row.get("score"))
    year = safe_int(date[:4], 0)

    match = {
        "match_id": build_match_id(year, gender, date, tournament, rnd, winner, loser),
        "date": date,
        "tournament": tournament,
        "surface": surface,
        "round": rnd,
        "player1": winner,
        "player2": loser,
        "winner": winner,
        "loser": loser,
        "score": score,
        "gender": gender,
        "best_of": safe_int(row.get("best_of")),
        "draw_size": safe_int(row.get("draw_size")),
        "minutes": safe_int(row.get("minutes")),
        "tourney_level": clean_text(row.get("tourney_level")),
        "tourney_id": clean_text(row.get("tourney_id")),
    }

    stats = [
        "w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon",
        "w_SvGms", "w_bpSaved", "w_bpFaced",
        "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon", "l_2ndWon",
        "l_SvGms", "l_bpSaved", "l_bpFaced",
    ]
    for key in stats:
        match[key] = safe_int(row.get(key))

    return match


def dedupe(matches: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for m in matches:
        key = (
            m.get("date", ""),
            m.get("gender", ""),
            m.get("tournament", ""),
            m.get("round", ""),
            m.get("player1", ""),
            m.get("player2", ""),
            m.get("score", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(m)

    out.sort(key=lambda x: (
        x.get("date", ""),
        x.get("tournament", ""),
        x.get("gender", ""),
        x.get("round", ""),
        x.get("player1", ""),
        x.get("player2", ""),
    ))
    return out


def build_events(year: int, matches: List[Dict]) -> List[Dict]:
    finals = [m for m in matches if m.get("round") == "F"]
    finals.sort(key=lambda x: (x.get("date", ""), x.get("gender", ""), x.get("tournament", "")))

    events = []
    seen = set()

    for m in finals:
        key = (m.get("tournament", ""), m.get("gender", ""), m.get("date", ""))
        if key in seen:
            continue
        seen.add(key)

        events.append({
            "year": year,
            "event": m.get("tournament", ""),
            "name": m.get("tournament", ""),
            "winner": m.get("winner", ""),
            "runnerUp": m.get("loser", ""),
            "surface": m.get("surface", ""),
            "score": m.get("score", ""),
            "date": m.get("date", ""),
            "end_date": m.get("date", ""),
            "category": "Women" if m.get("gender") == "F" else "Men",
            "draw": m.get("draw_size", ""),
            "gender": m.get("gender", ""),
            "tourney_level": m.get("tourney_level", ""),
        })

    return events


def save_year(year: int, matches: List[Dict]) -> None:
    events = build_events(year, matches)

    season_path = SEASONS_DIR / f"{year}.json"
    match_path = MATCHES_DIR / f"{year}.json"
    event_path = EVENTS_DIR / f"{year}.json"

    season_path.write_text(json.dumps(matches, indent=2, ensure_ascii=False), encoding="utf-8")
    match_path.write_text(json.dumps(matches, indent=2, ensure_ascii=False), encoding="utf-8")
    event_path.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved {year}: matches={len(matches)} events={len(events)}")


def build_year(year: int) -> None:
    print(f"\n=== {year} ===")
    matches: List[Dict] = []

    atp_rows = fetch_csv_rows(ATP_URL.format(year=year))
    print(f"ATP rows: {len(atp_rows)}")
    for row in atp_rows:
        m = row_to_match(row, "M")
        if m:
            matches.append(m)

    wta_rows = fetch_csv_rows(WTA_URL.format(year=year))
    print(f"WTA rows: {len(wta_rows)}")
    for row in wta_rows:
        m = row_to_match(row, "F")
        if m:
            matches.append(m)

    matches = dedupe(matches)
    save_year(year, matches)


def main() -> None:
    print("TENNIS HISTORY REBUILD")
    print(f"Years: {START_YEAR}-{END_YEAR}")

    for year in range(START_YEAR, END_YEAR + 1):
        try:
            build_year(year)
            time.sleep(0.2)
        except Exception as exc:
            print(f"FAILED {year}: {exc}")

    print("\nDONE")


if __name__ == "__main__":
    main()
