import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://thegolfnewsnet.com/list-of-mens-golf-major-championship-winners-by-year/"
OUTPUT_FILE = "docs/data/golf/pga_winners.json"

MAJORS = [
    "Masters Tournament",
    "U.S. Open",
    "The Open Championship",
    "PGA Championship"
]

START_YEAR = 1860
END_YEAR = 2026


# -----------------------
# FIX: US OPEN EARLY YEARS
# -----------------------
US_OPEN_FIX = {
    1895: "Horace Rawlins",
    1896: "James Foulis",
    1897: "Joe Lloyd",
    1898: "Fred Herd",
    1899: "Willie Smith",
    1900: "Harry Vardon",
    1901: "Willie Anderson",
    1902: "Laurie Auchterlonie",
    1903: "Willie Anderson",
    1904: "Willie Anderson",
    1905: "Willie Anderson",
    1906: "Alex Smith",
    1907: "Alex Ross",
    1908: "Fred McLeod",
    1909: "George Sargent",
    1910: "Alex Smith",
    1911: "John McDermott",
    1912: "John McDermott",
    1913: "Francis Ouimet",
    1914: "Walter Hagen"
}


# -----------------------
# CLEAN NAME
# -----------------------
def clean_name(name):
    if not name:
        return ""

    name = name.strip()

    # remove brackets
    name = re.sub(r"\s*\(.*?\)", "", name)

    # remove asterisks
    name = name.replace("*", "")

    # blank invalid
    if name.lower() in ["not played", "—", "-", ""]:
        return ""

    return name.strip()


# -----------------------
# SCRAPE (HEADER SAFE)
# -----------------------
def scrape():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")

    # headers
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

    col_map = {}
    for i, h in enumerate(headers):
        h = h.lower()

        if "masters" in h:
            col_map["Masters Tournament"] = i
        elif "u.s." in h:
            col_map["U.S. Open"] = i
        elif "open championship" in h or "the open" in h:
            col_map["The Open Championship"] = i
        elif "pga" in h:
            col_map["PGA Championship"] = i

    data = {}

    for r in rows[1:]:
        cols = [c.get_text(strip=True) for c in r.find_all("td")]

        if not cols:
            continue

        if not cols[0].isdigit():
            continue

        year = int(cols[0])
        data[year] = {}

        for event in MAJORS:
            idx = col_map.get(event)

            if idx is not None and idx < len(cols):
                data[year][event] = clean_name(cols[idx])
            else:
                data[year][event] = ""

    return data


# -----------------------
# BUILD DATASET
# -----------------------
def build():
    scraped = scrape()
    final = []

    for year in range(START_YEAR, END_YEAR + 1):

        for event in MAJORS:

            # fix early US Open
            if event == "U.S. Open" and year in US_OPEN_FIX:
                winner = US_OPEN_FIX[year]
            else:
                winner = scraped.get(year, {}).get(event, "")

            winner = clean_name(winner)

            final.append({
                "tour": "pga",
                "year": year,
                "event": event,
                "winner": winner,
                "major": True,
                "score": "",
                "venue": "",
                "country": ""
            })

    final.sort(key=lambda x: (x["event"], x["year"]))
    return final


# -----------------------
# SAVE
# -----------------------
def save(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    data = build()
    save(data)

    print(f"Majors rebuilt correctly: {len(data)} rows")
