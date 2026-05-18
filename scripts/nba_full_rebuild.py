"""
Debug script — run this to see exactly what BeautifulSoup finds on a real page.
Usage: python scripts/debug_boxscore.py
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

# A known 1975 game from the screenshot
URL = "https://www.basketball-reference.com/boxscores/197510230ATL.html"

time.sleep(4)
r = requests.get(URL, headers=HEADERS, timeout=30)
print(f"HTTP {r.status_code}, {len(r.text)} bytes")

raw_html = r.text

# 1. How many HTML comments are there total?
soup = BeautifulSoup(raw_html, "lxml")
comments = soup.find_all(string=lambda t: isinstance(t, Comment))
print(f"\nTotal HTML comments found: {len(comments)}")
table_comments = [c for c in comments if "<table" in c]
print(f"Comments containing <table>: {len(table_comments)}")

# 2. How many tables before uncommenting?
tables_before = soup.find_all("table")
print(f"\nTables BEFORE uncommenting: {len(tables_before)}")
for t in tables_before:
    print(f"  id={t.get('id', '(no id)')}")

# 3. Check for box- tables directly in raw HTML
box_tables_in_raw = re.findall(r'id="(box-\w+-game-basic)"', raw_html)
print(f"\nbox-*-game-basic table IDs in raw HTML: {box_tables_in_raw}")

# 4. Are those IDs inside comments?
for tid in box_tables_in_raw:
    in_comment = any(tid in c for c in comments)
    print(f"  '{tid}' is inside a comment: {in_comment}")

# 5. Try uncommenting and re-check
def uncomment_html(soup):
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if "<table" in comment:
            new_soup = BeautifulSoup(comment, "lxml")
            comment.replace_with(new_soup)
    return soup

soup2 = BeautifulSoup(raw_html, "lxml")
soup2 = uncomment_html(soup2)
tables_after = soup2.find_all("table")
print(f"\nTables AFTER uncommenting: {len(tables_after)}")
for t in tables_after:
    print(f"  id={t.get('id', '(no id)')}")

box_tables_after = soup2.find_all("table", id=re.compile(r"^box-\w+-game-basic$"))
print(f"\nbox-*-game-basic tables found after uncommenting: {len(box_tables_after)}")
for t in box_tables_after:
    tbody = t.find("tbody")
    rows = tbody.find_all("tr") if tbody else []
    print(f"  {t['id']}: {len(rows)} rows in tbody")

