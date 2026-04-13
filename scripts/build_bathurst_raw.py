import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import re
import time

print("BATHURST RAW BUILDER (FINAL + LOCKED EARLY YEAR)")

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


# ---------------- LOCKED DATA ----------------
def locked_early_years(year):
    if year != 1963:
        return None

    return [
        {"year":1963,"finish":1,"driver1":"Bob Jane","driver2":"Harry Firth","car":"Ford Cortina"},
        {"year":1963,"finish":2,"driver1":"Doug Chivas","driver2":"Ken Wilkinson","car":"Morris Cooper"},
        {"year":1963,"finish":3,"driver1":"Jim McKeown","driver2":"George Reynolds","car":"Volkswagen 1200"},
        {"year":1963,"finish":4,"driver1":"Tony Allen","driver2":"Tony Reynolds","car":"Valiant AP5"},
        {"year":1963,"finish":5,"driver1":"Greg Mackie","driver2":"Graham White","car":"Volkswagen 1200"},
        {"year":1963,"finish":6,"driver1":"Bill Stanley","driver2":"John Alexander","car":"Morris 850"},
        {"year":1963,"finish":7,"driver1":"Barry Seton","driver2":"Herb Taylor","car":"Morris 850"},
        {"year":1963,"finish":8,"driver1":"Frank Matich","driver2":"George Murray","car":"Volkswagen 1200"},
        {"year":1963,"finish":9,"driver1":"Spencer Martin","driver2":"Brian Muir","car":"Holden EH"},
        {"year":1963,"finish":10,"driver1":"Brian Foley","driver2":"Peter Manton","car":"Morris Cooper"},
    ]


# ---------------- URL ----------------
def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000",
        f"{year}_AMP_Bathurst_1000"
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


# ---------------- FIND TABLE ----------------
def find_results_table(soup):
    best = None
    best_score = 0

    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()

        score = 0
        if "driver" in text: score += 3
        if "pos" in text or "position" in text: score += 3
        if "car" in text or "make" in text: score += 2

        if score > best_score:
            best_score = score
            best = table

    return best


# ---------------- DRIVER CHECK ----------------
def looks_like_person(name):
    name = clean(name)

    if any(c.isdigit() for c in name):
        return False

    bad = [
        "ford","holden","morris","volkswagen","vw","simca","triumph",
        "mini","cortina","falcon","torana","commodore","nissan",
        "motors","ltd","pty","team","sales","co","dealer"
    ]

    lower = name.lower()
    if any(b in lower for b in bad):
        return False

    return len(name.split()) >= 2


# ---------------- DRIVER EXTRACT ----------------
def extract_drivers(td):
    names = []

    for a in td.find_all("a"):
        n = clean(a.get_text())
        if looks_like_person(n) and n not in names:
            names.append(n)

    if len(names) >= 2:
        return names[:2]

    # fallback split
    raw = clean(td.get_text())
    parts = re.split(r"/|&|,| and ", raw)

    for p in parts:
        p = clean(p)
        if looks_like_person(p) and p not in names:
            names.append(p)

    return names[:2]


# ---------------- FINISH ----------------
def parse_finish(tr):
    for c in tr.find_all(["td","th"]):
        txt = clean(c.get_text())
        if txt.isdigit():
            return int(txt)
    return None


# ---------------- PARSE YEAR ----------------
def parse_year(year):

    # 🔥 LOCKED YEARS
    locked = locked_early_years(year)
    if locked:
        print(f"🔒 Locked {year}")
        return locked

    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return []

    print(f"Fetching {year}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        print(f"❌ Failed {year}")
        return []

    table = find_results_table(soup)

    if not table:
        print(f"❌ No table {year}")
        return []

    rows = []
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

        if not drivers:
            continue

        if len(drivers) == 1:
            drivers.append("Unknown")

        # CAR DETECTION
        car = ""
        for td in tds:
            txt = clean(td.get_text())
            if txt and txt not in drivers and not txt.isdigit():
                if any(x in txt.lower() for x in ["ford","holden","morris","volkswagen","simca","triumph"]):
                    car = txt
                    break

        row = {
            "year": year,
            "finish": finish,
            "driver1": drivers[0],
            "driver2": drivers[1],
            "car": car
        }

        existing = by_finish.get(finish)

        if not existing:
            by_finish[finish] = row
        else:
            if existing["driver2"] == "Unknown" and row["driver2"] != "Unknown":
                by_finish[finish] = row

    clean_rows = list(by_finish.values())
    clean_rows.sort(key=lambda x: x["finish"])

    return clean_rows


# ---------------- BUILD ----------------
all_rows = []

for year in range(START_YEAR, END_YEAR + 1):
    all_rows.extend(parse_year(year))
    time.sleep(1)

all_rows.sort(key=lambda x: (x["year"], x["finish"]))

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["year","finish","driver1","driver2","car"]
    )
    writer.writeheader()
    writer.writerows(all_rows)

print(f"🔥 DONE — {len(all_rows)} rows written")
