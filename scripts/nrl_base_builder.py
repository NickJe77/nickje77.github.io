import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("NRL BASE BUILDER (SAFE + MERGE)")

SEASON = 2026
URL = "https://www.nrl.com/draw/"

OUTPUT = Path(f"docs/data/nrl/seasons/{SEASON}.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# -------------------------------------------------
# LOAD EXISTING DATA (CRITICAL)
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
# PARSE MATCHES
# -------------------------------------------------
def parse(html):

    soup = BeautifulSoup(html, "html.parser")

    games = []

    links = soup.select("a[href*='/draw/']")

    for a in links:

        text = a.get_text(" ", strip=True)

        if "vs" not in text:
            continue

        try:
            parts = text.split()

            home = parts[parts.index("vs") - 1]
            away = parts[parts.index("vs") + 1]

            games.append({
                "season": SEASON,
                "home_team": home,
                "away_team": away
            })

        except:
            continue

    return games


# -------------------------------------------------
# MERGE DATA (NO DUPES)
# -------------------------------------------------
def merge(existing, new):

    seen = set()

    merged = []

    for g in existing + new:
        key = f"{g.get('home_team')}_{g.get('away_team')}"
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
    new_games = parse(html)

    # 🚨 SAFETY CHECK
    if len(new_games) < 5:
        print("❌ ABORTED: Scrape failed — keeping existing data")
        return

    merged = merge(existing, new_games)

    OUTPUT.write_text(json.dumps(merged, indent=2))

    print(f"Saved {len(merged)} games (merged safely)")


if __name__ == "__main__":
    main()
