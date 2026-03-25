import requests, time, random, json, re, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.pro-football-reference.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def sleep():
    t = random.uniform(10, 18)
    print(f"Sleep {t:.1f}s")
    time.sleep(t)

def fetch(url):
    for i in range(5):
        sleep()
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            print("GET", r.status_code, url)
            if r.status_code == 200:
                return r.text
        except:
            pass
        time.sleep(20)
    return None

def get_games(season):
    url = f"{BASE}/years/{season}/games.htm"
    html = fetch(url)
    if not html:
        return []

    html = re.sub(r"<!--|-->", "", html)
    soup = BeautifulSoup(html, "html.parser")

    games = {}

    for a in soup.find_all("a", href=True):
        if "/boxscores/" in a["href"]:
            gid = a["href"].split("/")[-1].replace(".htm", "")
            games[gid] = urljoin(BASE, a["href"])

    return sorted(games.items())

def parse_game(gid, html):
    html = re.sub(r"<!--|-->", "", html)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.text if soup.title else ""

    teams = []
    for t in soup.select(".team"):
        name = t.find("a")
        score = t.find("div", class_="score")
        teams.append({
            "team": name.text if name else None,
            "score": score.text if score else None
        })

    tables = {}
    for table in soup.find_all("table"):
        tid = table.get("id") or f"table_{len(tables)}"
        rows = []

        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue

            row = {}
            for i, c in enumerate(cells):
                key = c.get("data-stat") or f"col_{i}"
                row[key] = c.text.strip()

            rows.append(row)

        tables[tid] = rows

    return {
        "game_id": gid,
        "title": title,
        "teams": teams,
        "tables": tables
    }

def run(season):
    print("SEASON", season)

    games = get_games(season)
    print("FOUND", len(games), "games")

    base_dir = f"docs/data/nfl/games/{season}"
    os.makedirs(base_dir, exist_ok=True)

    for gid, url in games:
        out = f"{base_dir}/{gid}.json"

        if os.path.exists(out):
            print("SKIP", gid)
            continue

        html = fetch(url)
        if not html:
            print("FAILED", gid)
            continue

        data = parse_game(gid, html)

        with open(out, "w") as f:
            json.dump(data, f, indent=2)

        print("SAVED", gid)

        if random.random() < 0.2:
            t = random.uniform(30, 60)
            print("LONG PAUSE", t)
            time.sleep(t)

if __name__ == "__main__":
    import sys
    season = int(sys.argv[1])
    run(season)
