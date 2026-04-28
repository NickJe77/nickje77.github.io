import os, re, json, time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright

YEAR = int(os.environ.get("YEAR", "1970"))

BASE_DIR = "docs/data/nfl"
SEASON_DIR = f"{BASE_DIR}/seasons"
BOX_DIR = f"{BASE_DIR}/boxscores"

PFR = "https://www.pro-football-reference.com"

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(BOX_DIR, exist_ok=True)

def clean(x):
    return re.sub(r"\s+", " ", str(x)).strip()

def gid(h):
    m = re.search(r"/boxscores/(.+)\.htm", h or "")
    return m.group(1) if m else None

def rnd(w):
    w = clean(w).lower()
    if "wild" in w: return "Wild Card"
    if "div" in w: return "Divisional"
    if "conf" in w: return "Conference Championship"
    if "super" in w: return "Super Bowl"
    return "Regular Season"

def get(page, url):
    print("GET", url)
    page.goto(url, timeout=60000)
    time.sleep(2)
    html = page.content()
    if "Access denied" in html or "403" in html:
        raise Exception("Blocked")
    return html

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print(f"=== BUILDING {YEAR} ===")

    html = get(page, f"{PFR}/years/{YEAR}/games.htm")
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="games")
    games = []

    for r in table.select("tbody tr"):
        if "thead" in r.get("class", []): continue
        a = r.select_one('td[data-stat="boxscore_word"] a')
        if not a: continue

        games.append({
            "game_id": gid(a["href"]),
            "url": PFR + a["href"],
            "date": clean(r.select_one('td[data-stat="game_date"]').text),
            "winner": clean(r.select_one('td[data-stat="winner"]').text),
            "loser": clean(r.select_one('td[data-stat="loser"]').text),
            "pts_w": clean(r.select_one('td[data-stat="pts_win"]').text),
            "pts_l": clean(r.select_one('td[data-stat="pts_lose"]').text),
            "round": rnd(r.select_one('th[data-stat="week_num"]').text)
        })

    year_dir = f"{BOX_DIR}/{YEAR}"
    os.makedirs(year_dir, exist_ok=True)

    season = []

    for g in games:
        try:
            html = get(page, g["url"])
            soup = BeautifulSoup(html, "html.parser")

            for c in soup.find_all(string=lambda x: isinstance(x, Comment)):
                try:
                    cs = BeautifulSoup(c, "html.parser")
                    for t in cs.find_all("table"):
                        soup.append(t)
                except: pass

            stats = {}
            for t in soup.find_all("table"):
                tid = t.get("id")
                if not tid: continue
                try:
                    df = pd.read_html(str(t))[0]
                    df.columns = [clean(c) for c in df.columns]
                    stats[tid] = df.to_dict("records")
                except: continue

            with open(f"{year_dir}/{g['game_id']}.json","w") as f:
                json.dump({
                    "game_id": g["game_id"],
                    "date": g["date"],
                    "winner": f"{g['winner']} {g['pts_w']}",
                    "loser": f"{g['loser']} {g['pts_l']}",
                    "round": g["round"],
                    "player_stats": stats
                }, f)

            season.append({
                "game_id": g["game_id"],
                "date": g["date"],
                "winner": f"{g['winner']} {g['pts_w']}",
                "loser": f"{g['loser']} {g['pts_l']}",
                "round": g["round"],
                "boxscore_file": f"/data/nfl/boxscores/{YEAR}/{g['game_id']}.json"
            })

            print("OK", g["game_id"])

        except Exception as e:
            print("FAIL", g["game_id"], e)

        time.sleep(2)

    with open(f"{SEASON_DIR}/{YEAR}.json","w") as f:
        json.dump({"year": YEAR, "games": season}, f)

    browser.close()

print("DONE", YEAR)
