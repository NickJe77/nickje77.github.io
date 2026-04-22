```python
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SERIES_ID = "1510719"
OUT_FILE = Path("docs/data/ipl/seasons/2026.json")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Match ids on Cricinfo appear sequential for IPL 2026.
# Example results confirm:
# 21st match = 1529264
# 25th match = 1529268
# 30th match = 1529273
# 31st match = 1529274
# 32nd match = 1529275
# So we scan the full 2026 tournament range safely.
MATCH_ID_START = 1529244
MATCH_ID_END = 1529317

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"https://www.espncricinfo.com/series/ipl-2026-{SERIES_ID}",
}

session = requests.Session()
session.headers.update(HEADERS)


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def safe_int(value, default=0):
    try:
        return int(str(value).strip())
    except Exception:
        return default


def balls_to_overs(balls):
    whole = balls // 6
    rem = balls % 6
    return f"{whole}.{rem}"


def extract_json_candidates(html):
    candidates = []

    # __NEXT_DATA__
    m = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        try:
            candidates.append(json.loads(m.group(1)))
        except Exception:
            pass

    # window.__INITIAL_STATE__ / similar blobs
    for pat in [
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;</script>",
        r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\})\s*;</script>",
    ]:
        for mm in re.finditer(pat, html, re.DOTALL | re.IGNORECASE):
            try:
                candidates.append(json.loads(mm.group(1)))
            except Exception:
                pass

    return candidates


def walk_find_scorecard(node):
    """
    Recursively search for structures that look like batting/bowling scorecard data.
    """
    hits = []

    def _walk(obj):
        if isinstance(obj, dict):
            keys = set(obj.keys())

            # common scorecard-ish containers
            if (
                {"innings"} <= keys
                or {"batting", "bowling"} <= keys
                or {"scorecard"} <= keys
                or {"inning", "inningNumber"} <= keys
            ):
                hits.append(obj)

            for v in obj.values():
                _walk(v)

        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(node)
    return hits


def parse_tables_from_html(soup):
    """
    Fallback parser from visible HTML tables if JSON blobs are unavailable.
    """
    tables = soup.find_all("table")
    parsed_tables = []

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        header = []
        first = rows[0].find_all(["th", "td"])
        for c in first:
            header.append(clean_text(c.get_text(" ", strip=True)))

        body = []
        for row in rows[1:]:
            cols = row.find_all(["th", "td"])
            values = [clean_text(c.get_text(" ", strip=True)) for c in cols]
            if any(values):
                body.append(values)

        if header and body:
            parsed_tables.append({"header": header, "rows": body})

    return parsed_tables


def parse_match(match_id):
    url = (
        f"https://www.espncricinfo.com/series/ipl-2026-{SERIES_ID}/"
        f"match-{match_id}/full-scorecard"
    )

    r = session.get(url, timeout=30, allow_redirects=True)

    if r.status_code != 200:
        print(f"SKIP {match_id}: status {r.status_code}")
        return None

    html = r.text

    if "full scorecard" not in html.lower() and "scorecard" not in html.lower():
        print(f"SKIP {match_id}: no scorecard content")
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")

    match = {
        "match_id": str(match_id),
        "series_id": SERIES_ID,
        "source_url": r.url,
        "title": title,
        "date": "",
        "ground": "",
        "city": "",
        "teams": [],
        "result": "",
        "player_of_match": "",
        "innings": [],
    }

    # Meta text
    page_text = clean_text(soup.get_text(" ", strip=True))

    # Try to pull a readable result line
    result_patterns = [
        r"([A-Za-z .&'-]+ won by [^\.]+)",
        r"([A-Za-z .&'-]+ beat [A-Za-z .&'-]+ by [^\.]+)",
        r"(Match tied[^\.]*)",
        r"(No result[^\.]*)",
    ]
    for pat in result_patterns:
        mm = re.search(pat, page_text, re.IGNORECASE)
        if mm:
            match["result"] = clean_text(mm.group(1))
            break

    # Try JSON blobs first
    candidates = extract_json_candidates(html)
    scorecard_hits = []
    for c in candidates:
        scorecard_hits.extend(walk_find_scorecard(c))

    # Pull visible tables as fallback
    visible_tables = parse_tables_from_html(soup)

    match["raw_table_count"] = len(visible_tables)

    # Very defensive extraction from JSON hits
    for hit in scorecard_hits:
        if isinstance(hit, dict):
            # title-ish fields
            if not match["date"]:
                for k in ["date", "startDate", "start_date"]:
                    if k in hit and hit[k]:
                        match["date"] = clean_text(hit[k])
                        break

            if not match["ground"]:
                for k in ["ground", "venue", "location"]:
                    if k in hit and hit[k]:
                        if isinstance(hit[k], dict):
                            match["ground"] = clean_text(
                                hit[k].get("name") or hit[k].get("longName") or ""
                            )
                            match["city"] = clean_text(
                                hit[k].get("town") or hit[k].get("city") or ""
                            )
                        else:
                            match["ground"] = clean_text(hit[k])
                        break

            if not match["teams"]:
                for k in ["teams", "team", "team1", "team2"]:
                    if k in hit:
                        val = hit[k]
                        if isinstance(val, list):
                            names = []
                            for item in val:
                                if isinstance(item, dict):
                                    names.append(
                                        clean_text(
                                            item.get("teamName")
                                            or item.get("name")
                                            or item.get("longName")
                                            or item.get("abbreviation")
                                            or ""
                                        )
                                    )
                                else:
                                    names.append(clean_text(item))
                            names = [x for x in names if x]
                            if len(names) >= 2:
                                match["teams"] = names[:2]
                                break

            innings = hit.get("innings")
            if isinstance(innings, list) and innings and not match["innings"]:
                for inn in innings:
                    inning = {
                        "team": "",
                        "score": "",
                        "overs": "",
                        "batting": [],
                        "bowling": [],
                    }

                    if isinstance(inn, dict):
                        team_val = inn.get("team") or inn.get("teamName")
                        if isinstance(team_val, dict):
                            inning["team"] = clean_text(
                                team_val.get("teamName")
                                or team_val.get("name")
                                or team_val.get("longName")
                                or ""
                            )
                        else:
                            inning["team"] = clean_text(team_val)

                        if inn.get("score"):
                            inning["score"] = clean_text(inn.get("score"))
                        elif inn.get("runs") is not None:
                            score = f'{inn.get("runs")}/{inn.get("wickets", "")}'
                            inning["score"] = clean_text(score)

                        if inn.get("overs"):
                            inning["overs"] = clean_text(inn.get("overs"))

                        # batting
                        for section_key in ["batting", "batters", "batsmen"]:
                            rows = inn.get(section_key)
                            if isinstance(rows, list):
                                for row in rows:
                                    if isinstance(row, dict):
                                        inning["batting"].append(
                                            {
                                                "player": clean_text(
                                                    row.get("name")
                                                    or row.get("playerName")
                                                    or row.get("batter")
                                                    or ""
                                                ),
                                                "dismissal": clean_text(
                                                    row.get("dismissal")
                                                    or row.get("howOut")
                                                    or ""
                                                ),
                                                "runs": clean_text(row.get("runs", "")),
                                                "balls": clean_text(row.get("balls", "")),
                                                "fours": clean_text(
                                                    row.get("fours", row.get("4s", ""))
                                                ),
                                                "sixes": clean_text(
                                                    row.get("sixes", row.get("6s", ""))
                                                ),
                                                "sr": clean_text(
                                                    row.get("strikeRate")
                                                    or row.get("sr")
                                                    or ""
                                                ),
                                            }
                                        )
                                break

                        # bowling
                        for section_key in ["bowling", "bowlers"]:
                            rows = inn.get(section_key)
                            if isinstance(rows, list):
                                for row in rows:
                                    if isinstance(row, dict):
                                        balls = safe_int(row.get("balls", 0), 0)
                                        inning["bowling"].append(
                                            {
                                                "player": clean_text(
                                                    row.get("name")
                                                    or row.get("playerName")
                                                    or row.get("bowler")
                                                    or ""
                                                ),
                                                "overs": clean_text(
                                                    row.get("overs") or balls_to_overs(balls)
                                                ),
                                                "maidens": clean_text(
                                                    row.get("maidens", row.get("m", ""))
                                                ),
                                                "runs": clean_text(row.get("runs", "")),
                                                "wickets": clean_text(
                                                    row.get("wickets", row.get("w", ""))
                                                ),
                                                "econ": clean_text(
                                                    row.get("economy")
                                                    or row.get("econ")
                                                    or ""
                                                ),
                                            }
                                        )
                                break

                    if inning["team"] or inning["score"] or inning["batting"] or inning["bowling"]:
                        match["innings"].append(inning)

    # Fallback: if JSON extraction failed, keep visible tables so the season file
    # still has usable raw scorecard material for downstream processing.
    if not match["innings"] and visible_tables:
        match["raw_tables"] = visible_tables

    # Teams fallback from title
    if len(match["teams"]) < 2 and title:
        tt = re.search(r"Full Scorecard of (.+?) vs (.+?),", title, re.IGNORECASE)
        if tt:
            match["teams"] = [clean_text(tt.group(1)), clean_text(tt.group(2))]

    # Date fallback from title
    if not match["date"] and title:
        dm = re.search(r",\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", title)
        if dm:
            match["date"] = clean_text(dm.group(1))

    # Ground fallback from title
    if not match["ground"] and title:
        gm = re.search(r"at\s+(.+?),\s*[A-Za-z]+\s+\d{1,2},\s+\d{4}", title)
        if gm:
            match["ground"] = clean_text(gm.group(1))

    # Require at least a real scorecard page
    if not match["teams"] and not match["innings"] and not visible_tables:
        print(f"SKIP {match_id}: page fetched but no structured data")
        return None

    print(f"OK {match_id} {match['teams']}")
    return match


def main():
    all_matches = []

    for match_id in range(MATCH_ID_START, MATCH_ID_END + 1):
        try:
            match = parse_match(match_id)
            if match:
                all_matches.append(match)
            time.sleep(1.2)
        except Exception as e:
            print(f"FAIL {match_id}: {e}")

    # Sort by date then id where possible
    all_matches.sort(key=lambda x: (x.get("date", ""), x.get("match_id", "")))

    out = {
        "season": "2026",
        "series_id": SERIES_ID,
        "source": "ESPN Cricinfo full scorecards",
        "matches": all_matches,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"SAVED {OUT_FILE}")
    print(f"MATCHES {len(all_matches)}")


if __name__ == "__main__":
    main()
