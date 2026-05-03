import requests
from bs4 import BeautifulSoup
import os
import json
import time

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

# 🔑 Known working World Cup results page (TEST FIRST)
TEST_URL = "https://www.espncricinfo.com/series/icc-cricket-world-cup-2019-1144415/match-results"

# -----------------------------
# SAFE WRITE
# -----------------------------
def safe_write(path, data):
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------------
# STEP 1 — PROVE DATA
# -----------------------------
def get_links():

    print("Fetching:", TEST_URL)

    res = requests.get(TEST_URL, headers=HEADERS)

    print("STATUS:", res.status_code)

    soup = BeautifulSoup(res.text, "lxml")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/match/" in href:
            full = "https://www.espncricinfo.com" + href
            links.append(full)

    links = list(set(links))

    print("LINKS FOUND:", len(links))

    # print first few so we KNOW it worked
    for l in links[:10]:
        print("LINK:", l)

    return links

# -----------------------------
# STEP 2 — BASIC PARSE (guaranteed output)
# -----------------------------
def parse_match(url):

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    title = soup.find("title")

    if not title:
        return None

    return {
        "match": title.text.strip(),
        "date": "",
        "venue": "",
        "result": "",
        "innings": []
    }

# -----------------------------
# BUILD
# -----------------------------
def build():

    links = get_links()

    # 🔴 HARD STOP if no links (so we don't silently fail again)
    if not links:
        print("NO LINKS FOUND — STOPPING")
        return

    year = "2019"  # test year only to prove it works

    folder = f"{OUTPUT}/{year}"
    os.makedirs(folder, exist_ok=True)

    total = 0

    for link in links:

        match_id = link.split("/")[-1]
        path = f"{folder}/{match_id}.json"

        if os.path.exists(path):
            continue

        data = parse_match(link)

        if not data:
            continue

        safe_write(path, data)

        print("Saved:", match_id)
        total += 1

        time.sleep(0.2)

    print(f"\nBUILT {total} MATCHES")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    build()
    print("DONE")
