import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("IPL 2026 GAP FILLER")

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.espncricinfo.com"
SERIES_URL = "https://www.espncricinfo.com/series/ipl-2026-1510719/match-results"

headers = {"User-Agent": "Mozilla/5.0"}

# -------------------------
# LOAD EXISTING DATA
# -------------------------
existing = []
existing_ids = set()

if OUTPUT.exists():
    with open(OUTPUT) as f:
        existing = json.load(f)
        for m in existing:
            existing_ids.add(m.get("file"))

print("Existing matches:", len(existing))

# -------------------------
# GET MATCH LIST
# -------------------------
r = requests.get(SERIES_URL, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

links = []

for a in soup.select("a[href*='/match/']"):
    href = a.get("href")
    if "/full-scorecard" in href:
        links.append(href)

links = list(set(links))

print("Found links:", len(links))

new_matches = []

# -------------------------
# PROCESS EACH MATCH
# -------------------------
for link in links:

    match_id_match = re.search(r"/match/(\d+)", link)
    if not match_id_match:
        continue

    match_id = match_id_match.group(1)
    file_name = f"{match_id}.json"

    if file_name in existing_ids:
        continue

    try:
        url = BASE_URL + link
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        # -------------------------
        # TEAMS
        # -------------------------
        title = soup.title.text if soup.title else ""
        teams = []

        t = re.search(r"(.+?) vs (.+?),", title)
        if t:
            teams = [t.group(1).strip(), t.group(2).strip()]

        # -------------------------
        # RESULT
        # -------------------------
        result = ""
        r_match = re.search(r"([A-Za-z .]+ won by [^\.]+)", text)
        if r_match:
            result = r_match.group(1)

        # -------------------------
        # VENUE
        # -------------------------
        venue = ""
        v_match = re.search(r"at ([A-Za-z ,]+),", title)
        if v_match:
            venue = v_match.group(1)

        # -------------------------
        # BUILD MATCH (YOUR FORMAT)
        # -------------------------
        match = {
            "meta": {},
            "info": {
                "season": "2026",
                "teams": teams,
                "venue": venue,
                "outcome": {"result": result},
                "event": {"name": "Indian Premier League"}
            },
            "innings": [],
            "file": file_name
        }

        new_matches.append(match)

        print("✔ added", match_id)

        time.sleep(1)

    except Exception as e:
        print("fail", match_id)

# -------------------------
# MERGE + SAVE
# -------------------------
combined = existing + new_matches

with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

print("NEW:", len(new_matches))
print("TOTAL:", len(combined))
print("DONE")
