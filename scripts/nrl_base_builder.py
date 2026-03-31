import requests
import json
import re
from pathlib import Path

print("NRL BASE BUILDER (JSON EXTRACTION)")

SEASON = 2026
URL = f"https://www.nrl.com/draw/?competition=111&season={SEASON}"

OUTPUT = Path(f"docs/data/nrl/seasons/{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# -------------------------------------------------
# LOAD EXISTING DATA
# -------------------------------------------------
def load_existing():
    if OUTPUT.exists():
        try:
            return json.loads(OUTPUT.read_text())
        except:
            return []
    return []


# -------------------------------------------------
# FETCH PAGE
# -------------------------------------------------
def fetch():
    r = requests.get(URL, headers=HEADERS)
    return r.text


# -------------------------------------------------
# EXTRACT JSON FROM PAGE
# -------------------------------------------------
def extract_json(html):

    # find window.__INITIAL_STATE__
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*});', html)

    if not match:
        print("❌ Could not find embedded data")
        return []

    data = json.loads(match.group(1))

    games = []

    rounds = data.get("draw", {}).get("rounds", [])

    for rnd in rounds:
        round_num = rnd.get("roundNumber")

        for m in rnd.get("matches", []):

            games.append({
                "season": SEASON,
                "round": round_num,
                "home_team": m.get("homeTeam", {}).get("nickName"),
                "away_team": m.get("awayTeam", {}).get("nickName"),
                "home_score": m.get("homeScore"),
                "away_score": m.get("awayScore"),
                "venue": m.get("venue", {}).get("name"),
                "date": m.get("startTime")
            })

    return games


# -------------------------------------------------
# MERGE
# -------------------------------------------------
def merge(existing, new):

    seen = set()
    merged = []

    for g in existing + new:
        key = f"{g.get('round')}_{g.get('home_team')}_{g.get('away_team')}"
        if key not in seen:
            seen.add(key)
            merged.append(g)

    return merged


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():

    existing = load_existing()

    html = fetch()
    new_games = extract_json(html)

    if len(new_games) < 5:
        print("❌ ABORTED: No real data found")
        return

    merged = merge(existing, new_games)

    OUTPUT.write_text(json.dumps(merged, indent=2))

    print(f"✅ Saved {len(merged)} games")


if __name__ == "__main__":
    main()
