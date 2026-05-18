"""
Row-level debug — shows exactly what each row looks like in the tbody.
Usage: python scripts/debug_boxscore2.py
"""
import re
import time
import requests
from bs4 import BeautifulSoup, Comment

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

URL = "https://www.basketball-reference.com/boxscores/197510230ATL.html"

time.sleep(4)
r = requests.get(URL, headers=HEADERS, timeout=30)
print(f"HTTP {r.status_code}")

soup = BeautifulSoup(r.text, "lxml")

# Uncomment
for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
    if "<table" in comment:
        new_soup = BeautifulSoup(comment, "lxml")
        comment.replace_with(new_soup)

table = soup.find("table", id="box-NOJ-game-basic")
print(f"Table found: {table is not None}")

tbody = table.find("tbody") if table else None
print(f"tbody found: {tbody is not None}")

if tbody:
    rows = tbody.find_all("tr")
    print(f"Total rows: {len(rows)}\n")
    for i, row in enumerate(rows):
        classes = row.get("class", [])
        name_td = row.find("td", {"data-stat": "player"})
        reason_td = row.find("td", {"data-stat": "reason"})
        mp_td = row.find("td", {"data-stat": "mp"})

        name = name_td.get_text(strip=True) if name_td else "NO NAME TD"
        reason_text = reason_td.get_text(strip=True) if reason_td else "NO REASON TD"
        mp_val = mp_td.get_text(strip=True) if mp_td else "NO MP TD"

        print(f"Row {i}: classes={classes}")
        print(f"  name='{name}'  reason='{reason_text}'  mp='{mp_val}'")
        print(f"  All td data-stats: {[td.get('data-stat') for td in row.find_all('td')]}")
        print()
