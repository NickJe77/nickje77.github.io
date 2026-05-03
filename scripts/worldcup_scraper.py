import requests
from bs4 import BeautifulSoup

url = "https://www.espncricinfo.com/series/icc-cricket-world-cup-2019-1144415/match-results"

headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(url, headers=headers)

print("STATUS:", res.status_code)

soup = BeautifulSoup(res.text, "lxml")

links = []

for a in soup.find_all("a", href=True):
    if "/match/" in a["href"]:
        links.append(a["href"])

print("LINKS FOUND:", len(links))

for l in links[:10]:
    print(l)
