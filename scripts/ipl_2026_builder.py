import requests
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

print("IPL 2026 BUILDER (RESTORED)")

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------
# LOAD EXISTING DATA (SAFE)
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
# STEP 1: GET MATCH IDS (FIXED)
# -------------------------
series_url = "https://www.espncricinfo.com/series/ipl-2026-1510719"

r = requests.get(series_url, headers=HEADERS)
html = r.text

match_ids = sorted(set(re.findall(r"/match/(\d+)", html)))

print("Match IDs found:", len(match_ids))

# -------------------------
# STEP 2: FETCH SCORECARDS
# -------------------------
new_matches = []

for match_id in match_ids:

    file_name = f"{match_id}.json"

    if file_name in existing_ids:
        continue

    try:
        url = f"https://www.espncricinfo.com/series/ipl-2026-1510719/match-{match_id}/full-scorecard"
        res = requests.get(url, headers=HEADERS)

        if res.status_code != 200:
            print("skip", match_id)
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # -------------------------
        # BASIC MATCH INFO
        # -------------------------
        title = soup.title.text if soup.title else ""
        teams = []

        t = re.search(r"(.+?) vs (.+?),", title)
        if t:
            teams = [t.group(1).strip(), t.group(2).strip()]

        venue = ""
        v = re.search(r"at (.+?),", title)
        if v:
            venue = v.group(1)

        text = soup.get_text(" ", strip=True)

        result = ""
        r_match = re.search(r"([A-Za-z .]+ won by [^\.]+)", text)
        if r_match:
            result = r_match.group(1)

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
            "innings": [],  # keep structure intact
            "file": file_name
        }

        new_matches.append(match)

        print("✔ added", match_id)

    except Exception as e:
        print("fail", match_id)

# -------------------------
# STEP 3: MERGE + SAVE
# -------------------------
combined = existing + new_matches

with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

print("NEW:", len(new_matches))
print("TOTAL:", len(combined))
print("DONE")
