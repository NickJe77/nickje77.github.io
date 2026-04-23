import json
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

SERIES_ID = "1510719"
OUT_FILE = Path("docs/data/ipl/seasons/2026.json")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

MATCH_ID_START = 1529244
MATCH_ID_END = 1529317

session = requests.Session()

def get_next_data(html):
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        return None
    return json.loads(script.string)

def parse_match(match_id):
    url = f"https://www.espncricinfo.com/series/ipl-2026-{SERIES_ID}/match-{match_id}/full-scorecard"
    
    r = session.get(url)
    if r.status_code != 200:
        return None

    data = get_next_data(r.text)
    if not data:
        return None

    try:
        props = data["props"]["pageProps"]
        content = props["data"]["content"]

        match = {
            "match_id": str(match_id),
            "teams": [],
            "date": "",
            "venue": "",
            "result": "",
            "innings": []
        }

        # basic info
        header = content.get("header", {})
        if header:
            match["teams"] = [
                header.get("team1", {}).get("team", {}).get("name", ""),
                header.get("team2", {}).get("team", {}).get("name", "")
            ]
            match["venue"] = header.get("ground", {}).get("name", "")
            match["date"] = header.get("startDate", "")
            match["result"] = header.get("statusText", "")

        # innings
        innings = content.get("innings", [])

        for inn in innings:
            inning = {
                "team": inn.get("team", {}).get("name", ""),
                "runs": inn.get("score", {}).get("runs", 0),
                "wickets": inn.get("score", {}).get("wickets", 0),
                "overs": inn.get("score", {}).get("overs", ""),
                "batting": [],
                "bowling": []
            }

            # batting
            for b in inn.get("batsmen", []):
                inning["batting"].append({
                    "player": b.get("player", {}).get("name", ""),
                    "runs": b.get("runs", 0),
                    "balls": b.get("balls", 0),
                    "4s": b.get("fours", 0),
                    "6s": b.get("sixes", 0),
                    "dismissal": b.get("dismissalText", "")
                })

            # bowling
            for b in inn.get("bowlers", []):
                inning["bowling"].append({
                    "player": b.get("player", {}).get("name", ""),
                    "overs": b.get("overs", ""),
                    "runs": b.get("runs", 0),
                    "wickets": b.get("wickets", 0)
                })

            match["innings"].append(inning)

        return match

    except Exception:
        return None


def main():
    matches = []

    for match_id in range(MATCH_ID_START, MATCH_ID_END + 1):
        m = parse_match(match_id)
        if m:
            matches.append(m)
            print("✔", match_id)
        else:
            print("skip", match_id)

        time.sleep(1)

    out = {
        "season": "2026",
        "matches": matches
    }

    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print("DONE:", len(matches))


if __name__ == "__main__":
    main()
