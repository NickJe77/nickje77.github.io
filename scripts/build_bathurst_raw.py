import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import re
import time

print("BATHURST RAW BUILDER (FINAL STABLE)")

OUT = Path("docs/data/bathurst/raw/bathurst_full.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if x is None:
        return ""
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x


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


def build_header_map(table):
    for tr in table.find_all("tr"):
        ths = tr.find_all("th")
        if ths:
            return {i: clean(th.get_text()).lower() for i, th in enumerate(ths)}
    return {}


def find_col(header_map, keywords):
    for i, name in header_map.items():
        for k in keywords:
            if k in name:
                return i
    return None


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


def extract_drivers(td):
    names = []

    for a in td.find_all("a"):
        n = clean(a.get_text())
        if looks_like_person(n) and n not in names:
            names.append(n)

    if len(names) >= 2:
        return names[:2]

    # fallback
    raw = clean(td.get_text())
    parts = re.split(r"/|&|,| and ", raw)

    for p in parts:
        p = clean(p)
        if looks_like_person(p) and p not in names:
            names.append(p)

    return names[:2]


def parse_finish(tr):
    cells = tr.find_all(["td","th"])

    for c in cells:
        txt = clean(c.get_text())
        if txt.isdigit():
            return int(txt)

    return None


def fix_early_years(rows, year):
    if year > 1972:
        return rows

    fixed = []

    for r in rows:
        combined = f"{r['driver1']} {r['driver2']}"

        names = re.findall(r"[A-Z][a-z]+ [A-Z][a-z]+", combined)

        unique = []
        for n in names:
            if n not in unique:
                unique.append(n)

        if len(unique) >= 2:
            r["driver1"] = unique[0]
            r["driver2"] = unique[1]
        elif len(unique) == 1:
            r["driver1"] = unique[0]
            r["driver2"] = "Unknown"

        fixed.append(r)

    return fixed


def parse_year(year):
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

    header_map = build_header_map(table)

    driver_idx = find_col(header_map, ["driver"])

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

        if driver_idx is not None and driver_idx < len(tds):
            drivers = extract_drivers(tds[driver_idx])

        if len(drivers) < 2:
            best = []
            for td in tds:
                d = extract_drivers(td)
                if len(d) > len(best):
                    best = d
            drivers = best

        if not drivers:
            continue

        if len(drivers) == 1:
            drivers.append("Unknown")

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

    # 🔥 FIX EARLY YEARS
    clean_rows = fix_early_years(clean_rows, year)

    return clean_rows


# BUILD
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
