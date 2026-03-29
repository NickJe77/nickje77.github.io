import requests
import json
import time
import re
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.tennisexplorer.com"

HEADERS = {"User-Agent": "Mozilla/5.0"}

OUT_DIR = Path("docs/data/tennis/matches")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

# -------------------------
def get_tournaments(year):
    url = f"{BASE}/calendar/{year}/atp/"
    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.select("a"):
        href = a.get("href", "")
        if "/tournament/" in href:
            full = BASE + href
            if full not in links:
                links.append(full)

    print(f"{year}: found {len(links)} tournaments")
    return links

# -------------------------
def parse_score(row):
    cells = row.find_all("td")
    score = []

    for c in cells:
        t = c.get_text(strip=True)
        if re.match(r"^\d+$", t):
            score.append(t)

    pairs = []
    for i in range(0, len(score), 2):
        if i+1 < len(score):
            pairs.append(f"{score[i]}-{score[i+1]}")

    return " ".join(pairs)

# -------------------------
def parse_round(text):
    text = text.lower()

    if "final" in text:
        return "F"
    if "semi" in text:
        return "SF"
    if "quarter" in text:
        return "QF"
    if "round of 16" in text:
        return "R16"
    if "round of 32" in text:
        return "R32"
    if "round of 64" in text:
        return "R64"

    return ""

# -------------------------
def scrape_tournament(url, year):
    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1")
    tournament = clean(title.text) if title else "Unknown"

    rows = soup.select("table tr")

    matches = []
    current_round = ""

    for r in rows:

        text = clean(r.get_text())

        # detect round headers
        if "final" in text.lower() or "round" in text.lower():
            current_round = parse_round(text)
            continue

        links = r.select("a")
        if len(links) < 2:
            continue

        p1 = clean(links[0].text)
        p2 = clean(links[1].text)

        score = parse_score(r)

        if not p1 or not p2:
            continue

        matches.append({
            "tournament": tournament,
            "year": year,
            "round": current_round,
            "player1": p1,
            "player2": p2,
            "score": score
        })

    print(f"✓ {tournament}: {len(matches)} matches")
    return matches

# -------------------------
def build_year(year):

    all_matches = []
    tournaments = get_tournaments(year)

    for url in tournaments:
        try:
            matches = scrape_tournament(url, year)
            all_matches.extend(matches)
            time.sleep(1)
        except Exception as e:
            print("ERROR:", e)

    path = OUT_DIR / f"{year}.json"
    path.write_text(json.dumps(all_matches, indent=2))

    print(f"\nSaved {year}: {len(all_matches)} matches")

# -------------------------
if __name__ == "__main__":
    for year in [2025, 2026]:
        build_year(year)
