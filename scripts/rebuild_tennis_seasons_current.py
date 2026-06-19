import requests
import json
import os
from datetime import date
from io import BytesIO

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q", "--break-system-packages"])
    import openpyxl

BASE = "docs/data/tennis/seasons"
CURRENT_YEAR = date.today().year
PREV_YEAR = CURRENT_YEAR - 1

HEADERS = {"User-Agent": "tennis-seasons-updater/1.0 (github-actions)"}

STATIC_NAMES = {
    "tirante t.a.": "Tomas Agustin Tirante",
    "llamas ruiz p.": "Pedro Llamas Ruiz",
    "gea a.": "Adrian Gea",
    "davidovich fokina a.": "Alejandro Davidovich Fokina",
    "cina f.": "Flavio Cobolli",
    "zheng m.": "Zheng Juncheng",
    "pavlovic l.": "Luca Pavlovic",
    "royer v.": "Valentin Royer",
    "mpetshi g.": "Giovanni Mpetshi Perricard",
    "carreno busta p.": "Pablo Carreno Busta",
    "de minaur a.": "Alex De Minaur",
    "van assche l.": "Luca Van Assche",
    "jodar r.": "Rodrigo Jodar",
    "bautista agut r.": "Roberto Bautista Agut",
    "de jong j.": "Jesper De Jong",
    "ugo carabelli c.": "Camilo Ugo Carabelli",
    "faurel t.": "Titouan Faurel",
    "diaz acosta f.": "Facundo Diaz Acosta",
    "zhang zh.": "Zhang Zhizhen",
    "prado angelo j.c.": "Juan Carlos Prado Angelo",
    "struff j.l.": "Jan-Lennard Struff",
    "cerundolo j.m.": "Juan Manuel Cerundolo",
    "auger-aliassime f.": "Felix Auger-Aliassime",
    "tabur c.": "Clement Tabur",
    "kouame m.": "Mathis Hamou",
    "merida aguilar d.": "Daniel Merida Aguilar",
    "van de zandschulp b.": "Botic Van De Zandschulp",
    "tiafoe f.": "Frances Tiafoe",
    "fils a.": "Arthur Fils",
    "muller a.": "Alexandre Muller",
    "cazaux a.": "Arthur Cazaux",
    "baez s.": "Sebastian Baez",
    "cerundolo f.": "Francisco Cerundolo",
    "tabilo a.": "Alejandro Tabilo",
    "shelton b.": "Ben Shelton",
    "rune h.": "Holger Rune",
    "ruud c.": "Casper Ruud",
    "zverev a.": "Alexander Zverev",
    "alcaraz c.": "Carlos Alcaraz",
    "sinner j.": "Jannik Sinner",
    "medvedev d.": "Daniil Medvedev",
    "tsitsipas s.": "Stefanos Tsitsipas",
    "hurkacz h.": "Hubert Hurkacz",
    "rublev a.": "Andrey Rublev",
    "fritz t.": "Taylor Fritz",
    "paul t.": "Tommy Paul",
    "nakashima b.": "Brandon Nakashima",
    "kokkinakis t.": "Thanasi Kokkinakis",
    "duckworth j.": "James Duckworth",
    "rinderknech a.": "Arthur Rinderknech",
    "fonseca j.": "Joao Fonseca",
    "mensik j.": "Jakub Mensik",
    "berrettini m.": "Matteo Berrettini",
    "sonego l.": "Lorenzo Sonego",
    "musetti l.": "Lorenzo Musetti",
    "navone m.": "Mariano Navone",
    "humbert u.": "Ugo Humbert",
    "halys q.": "Quentin Halys",
    "blockx a.": "Alexander Blockx",
    "medjedovic h.": "Hamad Medjedovic",
    "borges n.": "Nuno Borges",
    "prizmic d.": "Dino Prizmic",
    "michelsen a.": "Alex Michelsen",
    "basavareddy n.": "Nishesh Basavareddy",
    "trungelliti m.": "Marco Trungelliti",
    "machac t.": "Tomas Machac",
    "kecmanovic m.": "Miomir Kecmanovic",
    "khachanov k.": "Karen Khachanov",
    "djokovic n.": "Novak Djokovic",
    "wawrinka s.": "Stan Wawrinka",
    "lehecka j.": "Jiri Lehecka",
    "shevchenko a.": "Alexander Shevchenko",
    "rodionov j.": "Jurij Rodionov",
    "fucsovics m.": "Marton Fucsovics",
    "kovacevic a.": "Aleksandar Kovacevic",
    "swiatek i.": "Iga Swiatek",
    "sabalenka a.": "Aryna Sabalenka",
    "gauff c.": "Coco Gauff",
    "rybakina e.": "Elena Rybakina",
    "pegula j.": "Jessica Pegula",
    "keys m.": "Madison Keys",
    "collins d.": "Danielle Collins",
    "navarro e.": "Emma Navarro",
    "andreeva m.": "Mirra Andreeva",
    "paolini j.": "Jasmine Paolini",
    "badosa p.": "Paula Badosa",
    "haddad maia b.": "Beatriz Haddad Maia",
    "muchova k.": "Karolina Muchova",
    "vondrousova m.": "Marketa Vondrousova",
    "ostapenko j.": "Jelena Ostapenko",
    "kasatkina d.": "Daria Kasatkina",
    "sakkari m.": "Maria Sakkari",
    "garcia c.": "Caroline Garcia",
    "azarenka v.": "Victoria Azarenka",
    "jabeur o.": "Ons Jabeur",
    "fernandez l.": "Leylah Fernandez",
    "raducanu e.": "Emma Raducanu",
    "kostyuk m.": "Marta Kostyuk",
    "mertens e.": "Elise Mertens",
    "bouzkova m.": "Marie Bouzkova",
    "tauson c.": "Clara Tauson",
    "linette m.": "Magda Linette",
    "putintseva y.": "Yulia Putintseva",
    "potapova a.": "Anastasia Potapova",
    "alexandrova e.": "Ekaterina Alexandrova",
    "samsonova l.": "Liudmila Samsonova",
    "zheng q.": "Qinwen Zheng",
    "wang x.": "Xinyu Wang",
    "wang xin.": "Xinyu Wang",
    "wang xiy.": "Xiyu Wang",
    "bassols m.": "Marina Bassols Ribera",
    "efremova k.": "Kamilla Efremova",
    "valentova t.": "Tereza Valentova",
    "sorribes tormo s.": "Sara Sorribes Tormo",
    "ruse e.g.": "Elena-Gabriela Ruse",
    "tagger l.": "Lina Tagger",
    "quevedo k.": "Katarina Quevedo",
    "rakotomanga rajaonah t.": "Tessah Rakotomanga Rajaonah",
    "haddad maia b.": "Beatriz Haddad Maia",
    "tomljanovic a.": "Ajla Tomljanovic",
    "selekhmeteva o.": "Oksana Selekhmeteva",
    "kovinic d.": "Danka Kovinic",
    "krejcikova b.": "Barbora Krejcikova",
    "blinkova a.": "Anna Blinkova",
    "burel c.": "Clara Burel",
    "kraus s.": "Sinja Kraus",
    "bronzetti l.": "Lucia Bronzetti",
    "bondar a.": "Anna Bondar",
    "marcinko p.": "Petra Marcinko",
    "joint m.": "Maya Joint",
    "gibson t.": "Talia Gibson",
    "jeanjean l.": "Leolia Jeanjean",
    "udvardy p.": "Panna Udvardy",
    "cristian j.": "Jaqueline Cristian",
    "sramkova r.": "Rebecca Sramkova",
    "maria t.": "Tatjana Maria",
    "erjavec v.": "Veronika Erjavec",
    "kenin s.": "Sofia Kenin",
    "stephens s.": "Sloane Stephens",
    "arango e.": "Emiliana Arango",
    "ferro f.": "Fiona Ferro",
    "sonmez z.": "Zeynep Sonmez",
    "yastremska d.": "Dayana Yastremska",
    "bucsa c.": "Cristina Bucsa",
    "jones e.": "Elizabeth Jones",
}

ROUND_MAP = {
    "1st round":     "R64",
    "2nd round":     "R32",
    "3rd round":     "R16",
    "4th round":     "R8",
    "quarterfinal":  "QF",
    "quarterfinals": "QF",
    "semifinal":     "SF",
    "semifinals":    "SF",
    "final":         "F",
    "the final":     "F",
    "round robin":   "RR",
    "robin":         "RR",
}

def normalise_round(r):
    return ROUND_MAP.get(str(r).strip().lower(), str(r).strip())


def build_name_lookup():
    lookup = dict(STATIC_NAMES)

    if not os.path.isdir(BASE):
        return lookup

    for filename in sorted(os.listdir(BASE)):
        if not filename.endswith(".json"):
            continue
        year = filename.replace(".json", "")
        if year in [str(CURRENT_YEAR), str(PREV_YEAR)]:
            continue
        path = os.path.join(BASE, filename)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            matches = data.get("matches", data) if isinstance(data, dict) else data
            for m in matches:
                for field in ("winner", "loser", "player1", "player2"):
                    full_name = m.get(field, "").strip()
                    if not full_name or len(full_name) < 3:
                        continue
                    parts = full_name.split()
                    if len(parts) >= 2:
                        abbrev = f"{parts[-1]} {parts[0][0].upper()}."
                        lookup[abbrev.lower()] = full_name
        except Exception as e:
            print(f"  ⚠️  Could not read {filename}: {e}")

    print(f"  📖 Name lookup: {len(lookup)} entries")
    return lookup


def resolve_name(abbrev, lookup):
    if not abbrev:
        return abbrev
    return lookup.get(abbrev.strip().lower(), abbrev)


def make_urls(year):
    return {
        "M": f"http://www.tennis-data.co.uk/{year}/{year}.xlsx",
        "F": f"http://www.tennis-data.co.uk/{year}w/{year}w.xlsx",
    }


def fetch(url, gender, name_lookup):
    r = requests.get(url, timeout=60, headers=HEADERS)
    if r.status_code == 404:
        print(f"  ⚠️  Not found (404): {url}")
        return []
    r.raise_for_status()

    wb = openpyxl.load_workbook(BytesIO(r.content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]

    def col(row, *names):
        for name in names:
            try:
                v = row[headers.index(name)]
                if v is not None and str(v).strip() != "":
                    return str(v).strip()
            except (ValueError, IndexError):
                pass
        return ""

    gender_char = "m" if gender == "M" else "f"

    matches = []
    for row in rows[1:]:
        raw_date = col(row, "Date")
        if not raw_date:
            continue

        if hasattr(raw_date, "strftime"):
            date_str = raw_date.strftime("%Y-%m-%d")
        else:
            date_str = str(raw_date).strip()[:10]

        winner     = resolve_name(col(row, "Winner"), name_lookup)
        loser      = resolve_name(col(row, "Loser"),  name_lookup)
        tournament = col(row, "Tournament")
        surface    = col(row, "Surface", "Court")
        round_     = normalise_round(col(row, "Round"))

        score = col(row, "Score", "score")
        if not score:
            sets = []
            for i in range(1, 6):
                w = col(row, f"W{i}")
                l = col(row, f"L{i}")
                if w and l:
                    sets.append(f"{w}-{l}")
            score = " ".join(sets)

        if not winner or not loser:
            continue

        tournament_slug = tournament.replace(" ", "-").lower()
        winner_slug     = winner.replace(" ", "-").lower()
        loser_slug      = loser.replace(" ", "-").lower()
        year_str        = date_str[:4]

        match_id = f"{year_str}_{gender_char}_{date_str}_{tournament_slug}_{round_.lower()}_{winner_slug}_{loser_slug}"

        matches.append({
            "match_id":      match_id,
            "date":          date_str,
            "tournament":    tournament,
            "surface":       surface,
            "round":         round_,
            "player1":       winner,
            "player2":       loser,
            "winner":        winner,
            "loser":         loser,
            "score":         score,
            "gender":        gender,
            "best_of":       3,
            "draw_size":     0,
            "minutes":       0,
            "tourney_level": "",
            "tourney_id":    "",
            "w_ace": 0, "w_df": 0, "w_svpt": 0, "w_1stIn": 0,
            "w_1stWon": 0, "w_2ndWon": 0, "w_SvGms": 0, "w_bpSaved": 0, "w_bpFaced": 0,
            "l_ace": 0, "l_df": 0, "l_svpt": 0, "l_1stIn": 0,
            "l_1stWon": 0, "l_2ndWon": 0, "l_SvGms": 0, "l_bpSaved": 0, "l_bpFaced": 0,
        })

    wb.close()
    return matches


def filter_past(matches, year):
    today = date.today().isoformat()
    if str(year) != str(date.today().year):
        return matches
    return [m for m in matches if m["date"] <= today]


def save(year, matches):
    os.makedirs(BASE, exist_ok=True)
    path = f"{BASE}/{year}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"matches": matches}, f, indent=2)
    print(f"  ✅ Saved {path} ({len(matches)} matches)")


def build_season(year, name_lookup):
    print(f"\n📅 Building {year}...")
    urls = make_urls(year)
    all_matches = []

    for gender, url in urls.items():
        label = "ATP" if gender == "M" else "WTA"
        print(f"  Fetching {label} {year}...")
        matches = fetch(url, gender, name_lookup)
        print(f"    → {len(matches)} matches")
        all_matches.extend(matches)

    if not all_matches:
        print(f"  ⚠️  No data found for {year}, skipping.")
        return

    filtered = filter_past(all_matches, year)
    removed  = len(all_matches) - len(filtered)
    if removed:
        print(f"  ({removed} future matches removed)")

    save(year, filtered)


def main():
    print("🔍 Building name lookup...")
    name_lookup = build_name_lookup()

    build_season(CURRENT_YEAR, name_lookup)
    build_season(PREV_YEAR, name_lookup)
    print("\n✅ DONE — files written to", BASE)


if __name__ == "__main__":
    main()
