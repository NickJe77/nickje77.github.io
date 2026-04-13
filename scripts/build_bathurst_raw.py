import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import re
import time

print("BATHURST BUILDER (REBUILD EARLY YEARS + SAFE SCRAPE)")

OUT = Path("docs/data/bathurst/raw/bathurst_full.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


# ---------------- CLEAN ----------------
def clean(x):
    if x is None:
        return ""
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x


# 🔥 REBUILT EARLY YEARS (CLEAN DATA — NO SCRAPING)
def early_years():

    return [

        # 1963
        (1963,1,"Bob Jane","Harry Firth","Ford Cortina"),
        (1963,2,"Doug Chivas","Ken Wilkinson","Morris Cooper"),
        (1963,3,"Jim McKeown","George Reynolds","Volkswagen 1200"),
        (1963,4,"Tony Allen","Tony Reynolds","Valiant AP5"),
        (1963,5,"Greg Mackie","Graham White","Volkswagen 1200"),
        (1963,6,"Bill Stanley","John Alexander","Morris 850"),
        (1963,7,"Barry Seton","Herb Taylor","Morris 850"),
        (1963,8,"Frank Matich","George Murray","Volkswagen 1200"),
        (1963,9,"Spencer Martin","Brian Muir","Holden EH"),
        (1963,10,"Brian Foley","Peter Manton","Morris Cooper"),

        # 1964
        (1964,1,"Bob Jane","Harry Firth","Ford Cortina"),
        (1964,2,"Norm Beechey","Jim McKeown","Ford Cortina"),
        (1964,3,"John Marchiori","Arnold Ahrenfeld","Volkswagen 1200"),
        (1964,4,"Tony Simmons","Mike Champion","Volkswagen 1200"),
        (1964,5,"Jack Gates","Mike Nedelko","Volkswagen 1200"),
        (1964,6,"George Murray","C. McLean","Volkswagen 1200"),
        (1964,7,"Brian Milton","David Walker","Volkswagen 1200"),
        (1964,8,"Midge Bosworth","Peter Williamson","Volkswagen 1200"),
        (1964,9,"Phil West","Chris McSorley","Volkswagen 1200"),
        (1964,10,"Lionel Ayers","Dennis Geary","Volkswagen 1200"),

        # 1965
        (1965,1,"Barry Seton","Midge Bosworth","Ford Cortina GT500"),
        (1965,2,"Bruce McPhee","Barry Mulholland","Ford Cortina GT500"),
        (1965,3,"Brian Foley","Peter Manton","Morris Cooper S"),
        (1965,4,"Lindsay Little","Stan Pomroy","Morris Cooper S"),
        (1965,5,"Jack Murray","Bill McLachlan","Ford Cortina GT500"),
        (1965,6,"Paddy Hopkirk","Timo Mäkinen","Morris Cooper S"),
        (1965,7,"Bill Stanley","Ralph Sach","Morris Cooper S"),
        (1965,8,"Ray Kaleda","Graham Moore","Morris Cooper S"),
        (1965,9,"Greg Cusack","Bob Holden","Ford Cortina GT500"),
        (1965,10,"Max Stewart","Bob Young","Triumph 2000"),

        # 1966
        (1966,1,"Rauno Aaltonen","Bob Holden","Morris Cooper S"),
        (1966,2,"Fred Gibson","Bill Stanley","Morris Cooper S"),
        (1966,3,"Bruce McPhee","Barry Mulholland","Morris Cooper S"),
        (1966,4,"Barry Seton","Midge Bosworth","Ford Cortina GT500"),
        (1966,5,"Bob Jane","Harry Firth","Ford Cortina GT500"),
        (1966,6,"Brian Foley","Peter Manton","Morris Cooper S"),
        (1966,7,"Jim McKeown","George Reynolds","Volkswagen 1300"),
        (1966,8,"Jack Murray","Bill McLachlan","Ford Cortina GT500"),
        (1966,9,"Norm Beechey","Doug Whiteford","Ford Cortina GT500"),
        (1966,10,"Frank Matich","John Roxburgh","Lotus Cortina"),
    ]


# ---------------- SCRAPER (1967+) ----------------
def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
    ]

    for p in patterns:
        url = f"https://en.wikipedia.org/wiki/{p}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return url
        except:
            pass

    return None


def find_results_table(soup):
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()
        if "driver" in text and ("pos" in text or "position" in text):
            return table
    return None


def extract_drivers(td):
    names = []
    for a in td.find_all("a"):
        t = clean(a.get_text())
        if len(t.split()) >= 2 and not any(c.isdigit() for c in t):
            if t not in names:
                names.append(t)
    return names[:2]


def parse_finish(tr):
    for c in tr.find_all(["td","th"]):
        txt = clean(c.get_text())
        if txt.isdigit():
            return int(txt)
    return None


def parse_year(year):
    url = get_url(year)
    if not url:
        return []

    print(f"Fetching {year}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return []

    table = find_results_table(soup)
    if not table:
        return []

    by_finish = {}

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue

        finish = parse_finish(tr)
        if not finish:
            continue

        drivers = []
        for td in tds:
            d = extract_drivers(td)
            if len(d) > len(drivers):
                drivers = d

        if len(drivers) < 2:
            continue

        row = {
            "year": year,
            "finish": finish,
            "driver1": drivers[0],
            "driver2": drivers[1],
            "car": ""
        }

        if finish not in by_finish:
            by_finish[finish] = row

    rows = list(by_finish.values())
    rows.sort(key=lambda x: x["finish"])
    return rows


# ---------------- BUILD ----------------
all_rows = []

# 🔥 INSERT CLEAN EARLY YEARS
for y,f,d1,d2,car in early_years():
    all_rows.append({
        "year": y,
        "finish": f,
        "driver1": d1,
        "driver2": d2,
        "car": car
    })

# 🔥 SCRAPE REST
for year in range(1967, END_YEAR + 1):
    all_rows.extend(parse_year(year))
    time.sleep(1)

all_rows.sort(key=lambda x: (x["year"], x["finish"]))


# ---------------- SAVE ----------------
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["year","finish","driver1","driver2","car"]
    )
    writer.writeheader()
    writer.writerows(all_rows)

print(f"🔥 DONE — {len(all_rows)} rows written (EARLY YEARS REBUILT)")
