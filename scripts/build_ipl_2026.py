import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

print("BUILD IPL 2026 FROM ESPNCRICINFO")

SERIES_ID = "1510719"
FIXTURES_URL = f"https://www.espncricinfo.com/series/ipl-2026-{SERIES_ID}/match-schedule-fixtures-and-results"

OUTPUT = Path("docs/data/ipl/ipl_2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# 🔥 STRONG HEADERS (ANTI-403)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.espncricinfo.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

session = requests.Session()
session.headers.update(HEADERS)


# 🔥 SAFE REQUEST FUNCTION (HANDLES 403)
def get(url, tries=5):
    last_err = None

    for attempt in range(tries):
        try:
            r = session.get(url, timeout=30, allow_redirects=True)

            if r.status_code == 403:
                print(f"⚠️ 403 BLOCKED (attempt {attempt+1})")
                time.sleep(5 + attempt * 3)
                continue

            if r.status_code == 200:
                return r

            last_err = Exception(f"HTTP {r.status_code}")

        except Exception as e:
            last_err = e

        time.sleep(2 + attempt)

    raise last_err


# 🔍 EXTRACT NEXT DATA
def extract_next_data(html):
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")

    if tag and tag.string:
        return json.loads(tag.string)

    raise Exception("No __NEXT_DATA__ found")


# 🔁 WALK JSON
def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for i in obj:
            yield from walk(i)


# 🧠 FIND MATCHES
def extract_matches(data):
    matches = []

    for node in walk(data):
        if not isinstance(node, dict):
            continue

        text = json.dumps(node).lower()

        if "team" in text and "match" in text and "status" in text:
            matches.append(node)

    return matches


# 🔧 NORMALISE MATCH
def normalise(node):
    def pick(*keys):
        for k in keys:
            if k in node and node[k]:
                return node[k]
        return None

    match_id = pick("objectId", "id", "matchId")

    teams = []
    if "teams" in node:
        for t in node["teams"][:2]:
            teams.append({
                "name": t.get("teamName") or t.get("name"),
                "short": t.get("teamSName")
            })

    return {
        "season": "2026",
        "match_id": str(match_id),
        "title": pick("title", "name"),
        "date": pick("startDate", "date"),
        "venue": pick("ground", "venue"),
        "status": pick("statusText", "status"),
        "teams": teams,
    }


# 🚀 RUN

print("Fetching fixtures page...")
r = get(FIXTURES_URL)

data = extract_next_data(r.text)

candidates = extract_matches(data)

print("Candidates found:", len(candidates))

matches = {}

for c in candidates:
    m = normalise(c)

    if not m["match_id"]:
        continue

    matches[m["match_id"]] = m

final = list(matches.values())

if not final:
    raise Exception("❌ No matches found (ESPN likely blocked or structure changed)")

# 💾 SAVE
with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print(f"✅ Saved {len(final)} matches to {OUTPUT}")
