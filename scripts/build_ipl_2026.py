import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

print("BUILD IPL 2026 FROM ESPNCRICINFO")

SERIES_ID = "1510719"
SERIES_URL = f"https://www.espncricinfo.com/series/ipl-2026-{SERIES_ID}"
FIXTURES_URL = f"{SERIES_URL}/match-schedule-fixtures-and-results"

OUTPUT = Path("docs/data/ipl/ipl_2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": SERIES_URL,
}


def clean_text(value):
    if value is None:
        return None
    value = str(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def slugify_player(name):
    if not name:
        return None
    s = name.lower().strip()
    s = s.replace(".", "")
    s = s.replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or None


def get(session, url, tries=3, sleep_sec=2):
    last_err = None
    for attempt in range(tries):
        try:
            r = session.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and r.text:
                return r
            last_err = Exception(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            last_err = e
        time.sleep(sleep_sec * (attempt + 1))
    raise last_err


def extract_next_data(html):
    soup = BeautifulSoup(html, "html.parser")

    # Primary: __NEXT_DATA__
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag and tag.string:
        try:
            return json.loads(tag.string)
        except Exception:
            pass

    # Fallback: any JSON script that looks like page props
    for script in soup.find_all("script"):
        text = script.string or script.get_text(" ", strip=False)
        if not text:
            continue

        if '"pageProps"' in text or '"props"' in text:
            text = text.strip()
            try:
                return json.loads(text)
            except Exception:
                pass

        # Generic JS assignment fallback
        m = re.search(r'__NEXT_DATA__\s*=\s*(\{.*\})\s*;?', text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass

    return None


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def pick(d, *keys):
    for key in keys:
        if isinstance(d, dict) and key in d and d[key] not in (None, "", [], {}):
            return d[key]
    return None


def parse_match_id_from_url(url):
    if not url:
        return None
    m = re.search(r"-(\d+)(?:/|$)", url)
    return m.group(1) if m else None


def normalize_team(team):
    if not isinstance(team, dict):
        return {"name": clean_text(team)}
    return {
        "name": clean_text(
            pick(team, "teamName", "longName", "name", "title", "label")
        ),
        "short_name": clean_text(
            pick(team, "teamSName", "shortName", "abbreviation", "slug")
        ),
        "score": clean_text(
            pick(team, "score", "scoreText", "teamScore", "displayScore")
        ),
    }


def normalize_innings(innings):
    out = []
    if not isinstance(innings, list):
        return out

    for inn in innings:
        if not isinstance(inn, dict):
            continue

        team = pick(inn, "team", "battingTeam")
        out.append({
            "team": clean_text(
                pick(team or {}, "teamName", "longName", "name", "title")
                or pick(inn, "teamName", "title")
            ),
            "runs": pick(inn, "runs"),
            "wickets": pick(inn, "wickets", "wkts"),
            "overs": clean_text(pick(inn, "overs", "o")),
            "score": clean_text(pick(inn, "score", "scoreText", "displayScore")),
        })

    return out


def looks_like_match_summary(d):
    if not isinstance(d, dict):
        return False

    text_blob = json.dumps(d, ensure_ascii=False).lower()

    has_match_id = (
        pick(d, "objectId", "object_id", "matchId", "match_id", "id") is not None
        or re.search(rf'/{SERIES_ID}/', text_blob)
        or re.search(r'-\d{6,8}', text_blob)
    )

    has_team_hint = (
        any(k in d for k in ["teams", "team", "team1", "team2"])
        or '"teamname"' in text_blob
        or '"longname"' in text_blob
    )

    has_match_hint = (
        any(k in d for k in ["status", "statusText", "title", "subtitle", "description"])
        or "match" in text_blob
        or "won by" in text_blob
        or "no result" in text_blob
    )

    return has_match_id and has_team_hint and has_match_hint


def extract_match_candidates(next_data):
    candidates = []

    if not next_data:
        return candidates

    for node in walk(next_data):
        if looks_like_match_summary(node):
            candidates.append(node)

    return candidates


def find_match_urls_from_html(html):
    urls = set()

    # Any series page link with a numeric match id at the end
    for match in re.finditer(
        rf'href="([^"]*/series/ipl-2026-{SERIES_ID}/[^"]*?-\d+(?:/[^"]*)?)"',
        html,
        flags=re.I,
    ):
        href = match.group(1)
        if "/points-table" in href or "/stats" in href:
            continue
        urls.add(urljoin("https://www.espncricinfo.com", href))

    return sorted(urls)


def canonical_scorecard_url(url):
    if not url:
        return None

    # Strip query/hash
    url = url.split("?")[0].split("#")[0].rstrip("/")

    # Convert known article/page variants to scorecard page
    url = re.sub(
        r"/(live-match-blog|live-cricket-score|ball-by-ball-commentary|match-preview|report)$",
        "/full-scorecard",
        url,
    )

    # If it already looks like a match page but has no terminal page type, append full-scorecard
    if re.search(r"-\d+$", url):
        url = url + "/full-scorecard"

    return url


def normalize_candidate(d, discovered_urls):
    raw_url = (
        pick(d, "href", "url", "link", "matchUrl", "matchURL")
        or pick(d.get("statusText", {}) if isinstance(d.get("statusText"), dict) else {}, "url")
    )

    slug = clean_text(pick(d, "slug", "seoTitle", "slugText"))
    object_id = clean_text(pick(d, "objectId", "object_id", "matchId", "match_id", "id"))

    if raw_url:
        raw_url = urljoin("https://www.espncricinfo.com", raw_url)

    # Try to derive a URL from discovered fixture-page URLs if needed
    if not raw_url and object_id:
        for u in discovered_urls:
            if f"-{object_id}" in u:
                raw_url = u
                break

    if not object_id and raw_url:
        object_id = parse_match_id_from_url(raw_url)

    if not raw_url and slug and object_id:
        raw_url = f"{SERIES_URL}/{slug}-{object_id}"

    teams = pick(d, "teams")
    team1 = pick(d, "team1")
    team2 = pick(d, "team2")

    normalized_teams = []
    if isinstance(teams, list):
        normalized_teams = [normalize_team(t) for t in teams[:2]]
    else:
        if team1:
            normalized_teams.append(normalize_team(team1))
        if team2:
            normalized_teams.append(normalize_team(team2))

    innings = normalize_innings(pick(d, "innings", "inningScores", "score", "scores"))

    venue = pick(d, "ground", "venue")
    if isinstance(venue, dict):
        venue_name = clean_text(pick(venue, "name", "longName", "title"))
        city = clean_text(pick(venue, "town", "city"))
    else:
        venue_name = clean_text(venue)
        city = None

    result = clean_text(
        pick(d, "statusText", "result", "summary", "description", "stateTitle")
    )
    if isinstance(result, dict):
        result = clean_text(pick(result, "text", "long", "short", "title"))

    title = clean_text(pick(d, "title", "matchTitle", "name"))
    subtitle = clean_text(pick(d, "subtitle", "subTitle", "description"))

    pom = pick(d, "playerOfTheMatch", "mom")
    if isinstance(pom, dict):
        pom_name = clean_text(pick(pom, "name", "longName", "title"))
    else:
        pom_name = clean_text(pom)

    toss = pick(d, "toss")
    if isinstance(toss, dict):
        toss = clean_text(pick(toss, "text", "description", "title"))
    else:
        toss = clean_text(toss)

    status = clean_text(pick(d, "status", "state", "stateText"))
    stage = clean_text(pick(d, "stage", "className", "format"))
    date = clean_text(pick(d, "date", "startDate", "startTime", "dateTime"))
    competition = clean_text(pick(d, "seriesName", "series", "tournament", "competition"))
    if isinstance(competition, dict):
        competition = clean_text(pick(competition, "name", "longName", "title"))

    return {
        "season": "2026",
        "competition": competition or "Indian Premier League",
        "match_id": object_id,
        "title": title,
        "subtitle": subtitle,
        "date": date,
        "venue": venue_name,
        "city": city,
        "status": status,
        "stage": stage,
        "result": result,
        "toss": toss,
        "player_of_the_match": pom_name,
        "teams": normalized_teams,
        "innings": innings,
        "url": raw_url,
        "scorecard_url": canonical_scorecard_url(raw_url) if raw_url else None,
    }


def enrich_from_scorecard(session, match):
    url = match.get("scorecard_url") or match.get("url")
    if not url:
        return match

    try:
        r = get(session, url)
        page_data = extract_next_data(r.text)
    except Exception as e:
        print(f"  scorecard fetch failed for {url}: {e}")
        return match

    if not page_data:
        return match

    best = None
    target_id = match.get("match_id")

    for node in walk(page_data):
        if not isinstance(node, dict):
            continue

        node_id = clean_text(pick(node, "objectId", "object_id", "matchId", "match_id", "id"))
        text_blob = json.dumps(node, ensure_ascii=False).lower()

        if target_id and node_id == target_id:
            if "teamname" in text_blob or "innings" in text_blob or "status" in text_blob:
                best = node
                break

    if not best:
        return match

    extra = normalize_candidate(best, discovered_urls=[])

    # Merge only when ESPN detail page has more info
    for key in [
        "title",
        "subtitle",
        "date",
        "venue",
        "city",
        "status",
        "stage",
        "result",
        "toss",
        "player_of_the_match",
        "teams",
        "innings",
        "url",
        "scorecard_url",
    ]:
        if extra.get(key):
            match[key] = extra[key]

    return match


session = requests.Session()

print("Fetching fixtures page...")
fixtures_response = get(session, FIXTURES_URL)
fixtures_html = fixtures_response.text

discovered_urls = find_match_urls_from_html(fixtures_html)
print("Discovered match URLs:", len(discovered_urls))

fixtures_data = extract_next_data(fixtures_html)
if not fixtures_data:
    raise RuntimeError("Could not extract __NEXT_DATA__ from fixtures page")

candidates = extract_match_candidates(fixtures_data)
print("Candidate match objects found:", len(candidates))

matches_by_id = {}

for cand in candidates:
    m = normalize_candidate(cand, discovered_urls)
    match_id = m.get("match_id")

    if not match_id:
        continue

    # IPL-only and 2026-only guard
    text_blob = json.dumps(m, ensure_ascii=False).lower()
    if "ipl" not in text_blob and "indian premier league" not in text_blob:
        continue
    if m.get("season") != "2026":
        continue

    current = matches_by_id.get(match_id)
    if not current:
        matches_by_id[match_id] = m
    else:
        # Prefer richer object
        old_score = sum(1 for v in current.values() if v not in (None, "", [], {}))
        new_score = sum(1 for v in m.values() if v not in (None, "", [], {}))
        if new_score > old_score:
            matches_by_id[match_id] = m

matches = list(matches_by_id.values())
matches.sort(key=lambda x: (x.get("date") or "", x.get("match_id") or ""))

print("Normalized matches:", len(matches))

# Optional detail enrichment
for i, match in enumerate(matches, start=1):
    print(f"Enriching {i}/{len(matches)}: {match.get('match_id')} {match.get('title') or ''}")
    enrich_from_scorecard(session, match)
    time.sleep(0.75)

# Final cleanup
final_matches = []
seen = set()

for m in matches:
    match_id = m.get("match_id")
    if not match_id or match_id in seen:
        continue
    seen.add(match_id)

    team_names = [t.get("name") for t in m.get("teams", []) if isinstance(t, dict) and t.get("name")]

    final_matches.append({
        "season": "2026",
        "match_id": match_id,
        "title": m.get("title"),
        "subtitle": m.get("subtitle"),
        "date": m.get("date"),
        "venue": m.get("venue"),
        "city": m.get("city"),
        "status": m.get("status"),
        "stage": m.get("stage"),
        "result": m.get("result"),
        "toss": m.get("toss"),
        "player_of_the_match": m.get("player_of_the_match"),
        "teams": m.get("teams", []),
        "team_names": team_names,
        "innings": m.get("innings", []),
        "url": m.get("url"),
        "scorecard_url": m.get("scorecard_url"),
    })

if not final_matches:
    raise RuntimeError("No IPL 2026 matches were extracted from ESPNcricinfo")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(final_matches, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(final_matches)} matches to {OUTPUT}")
