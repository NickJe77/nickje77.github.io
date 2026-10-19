"""
build_search_index.py

Builds the people index behind the homepage "Search any athlete, jockey or
trainer" box. Run from the repo root (the GitHub Action does this):

    python scripts/build_search_index.py

Reads every sport's existing data (docs/data/... plus the NBA and baseball
indexes in R2) and writes small shard files:

    docs/data/search/people_a.json ... people_z.json, people_0.json

A person is written into the shard for the first letter of EACH word of
their name, so "Matt Rowell" is in both people_m.json and people_r.json.
Searching "Rowell" only downloads people_r.json (a few hundred KB), and
searching "Smith" finds every Smith across every sport.

Each shard:
    {"src": [[label, url_template], ...],
     "p":   [[name, src_index, value_or_0, extra], ...]}
url = url_template with {v} replaced by encodeURIComponent(value or name).

Every link format below is copied from how the site's own pages link to
that profile page, so search results open exactly what the site already
shows.
"""

import csv
import glob
import io
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

DOCS = "docs"
DATA = f"{DOCS}/data"
OUT = f"{DATA}/search"
R2 = "https://pub-68c8b4322a9d4d7f9b875047b45ac7c6.r2.dev"

SOURCES = []          # [label, url_template]
SRC_IDX = {}
PEOPLE = {}           # (name, src) -> [name, src, value, extra]
COUNTS = defaultdict(int)


def src(label, template):
    if label not in SRC_IDX:
        SRC_IDX[label] = len(SOURCES)
        SOURCES.append([label, template])
    return SRC_IDX[label]


def add(label, template, name, value=None, extra=""):
    name = re.sub(r"\s+", " ", str(name or "")).strip().strip("'\"")
    if not name or len(name) < 2 or "?" in name or name.isdigit():
        return
    if not re.search(r"[A-Za-zÀ-ɏ]", name):
        return
    s = src(label, template)
    v = value if (value is not None and str(value) != name) else 0
    key = (name.lower(), s, str(v))
    if key in PEOPLE:
        if extra and not PEOPLE[key][3]:
            PEOPLE[key][3] = extra
        return
    PEOPLE[key] = [name, s, v, extra or ""]
    COUNTS[label] += 1


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        print(f"  skip {path}: {e}")
        return None


def fetch_json(url):
    try:
        import requests
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            return r.json()
        print(f"  skip {url}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  skip {url}: {e}")
    return None


def read_csv(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            rows = list(csv.DictReader(f))
        # header cells sometimes have stray spaces (" Margin", " Position")
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in rows]
    except Exception as e:
        print(f"  skip {path}: {e}")
        return []


def js_slugify(s):
    """Same as the soccer pages' slugify()."""
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def simple_slug(s):
    """nascar / supercars / bathurst: name.toLowerCase().replace(/[^a-z0-9]+/g,'-')"""
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower())


def years(seasons):
    ys = sorted({int(str(x)[:4]) for x in seasons if re.match(r"^\d{4}", str(x))})
    if not ys:
        return ""
    return str(ys[0]) if ys[0] == ys[-1] else f"{ys[0]}–{ys[-1]}"


# ── AFL ──────────────────────────────────────────────────────────────────────
# Mirrors afl-player.html's normalizeGame() so the link opens the same
# player the page itself would show.
AFL_ALIASES = {"Luke D-Uniacke": "Luke Davies-Uniacke", "Cooper D-Tytler": "Cooper Duff-Tytler"}
AFL_TEAMS = {"footscray": "Western Bulldogs", "south melbourne": "Sydney", "brisbane lions": "Brisbane",
             "brisbane bears": "Brisbane", "kangaroos": "North Melbourne", "gws giants": "GWS",
             "greater western sydney": "GWS"}


def afl_name(n, season, team):
    n = re.sub(r"[←-⇿]", "", n or "").strip().replace("’", "'")
    n = re.sub(r"\bO([A-Z][a-z])", r"O'\1", n)
    if n == "Gary Ablett" and season >= 2000:
        n = "Gary Ablett Jnr"
    if n == "Bailey Williams" and team == "West Coast":
        n = "Bailey J. Williams"
    if n == "Nathan Brown" and team in ("Collingwood", "St Kilda"):
        n = "Nathan J. Brown"
    if n == "Nathan Brown" and team == "Melbourne":
        n = "Nathan Brown (Melbourne)"
    return AFL_ALIASES.get(n, n)


def build_afl():
    info = defaultdict(lambda: {"seasons": set(), "last": (0, "")})
    for path in glob.glob(f"{DATA}/afl/afl_*.json"):
        m = re.search(r"afl_(\d{4})\.json$", path)
        if not m:
            continue
        rows = load_json(path) or []
        for r in rows:
            season = int(r.get("season") or m.group(1))
            team = (r.get("played_for") or "").strip()
            team = AFL_TEAMS.get(team.lower(), team)
            n = afl_name(r.get("player"), season, team)
            if not n:
                continue
            i = info[n]
            i["seasons"].add(season)
            if season >= i["last"][0]:
                i["last"] = (season, team)
    for n, i in info.items():
        add("AFL", "afl-player.html?name={v}", n, None, f"{i['last'][1]} · {years(i['seasons'])}")


# ── NRL ──────────────────────────────────────────────────────────────────────
def build_nrl():
    info = defaultdict(lambda: {"seasons": set(), "team": ""})
    for path in glob.glob(f"{DATA}/nrl/seasons/*.json"):
        file_season = os.path.basename(path)[:4]
        for r in load_json(path) or []:
            # Two formats in the NRL files: one row per player, or one row
            # per match with a nested "players" list.
            plist = r.get("players") if isinstance(r.get("players"), list) else [r]
            for p in plist:
                n = (p.get("player") or "").strip()
                if not n:
                    continue
                info[n]["seasons"].add(r.get("season") or file_season)
                info[n]["team"] = p.get("played_for") or p.get("team") or info[n]["team"]
    for n, i in info.items():
        add("NRL", "nrl-player.html?player={v}", n, None, f"{i['team']} · {years(i['seasons'])}".strip(" ·"))


# ── Football (soccer) leagues — all use playerSlug(p) = name--firstteam ──────
SOCCER = [
    ("Premier League", "epl", "epl-player.html"),
    ("La Liga", "la_liga", "laliga-player.html"),
    ("Serie A", "seriea", "seriea-player.html"),
    ("Bundesliga", "bundesliga", "bundesliga-player.html"),
    ("Ligue 1", "ligue1", "ligue1-player.html"),
    ("A-League", "aleague", "aleague-player.html"),
    ("MLS", "mls", "mls-player.html"),
    ("J-League", "jleague", "jleague-player.html"),
    ("Brazil Serie A", "brazilseriea", "brazilseriea-player.html"),
    ("Champions League", "ucl", "ucl-player.html"),
    # Women's World Cup left out: womens-wc-player.html loads
    # data/women's-wc/womens-world-cup/players.json, which isn't in the repo
    # (only a .zip is), so those profile pages can't load yet.
]


def build_soccer():
    for label, folder, page in SOCCER:
        for p in load_json(f"{DATA}/{folder}/players.json") or []:
            n = p.get("name")
            teams = p.get("teams") or []
            slug = js_slugify(n)
            first = js_slugify(teams[0]) if teams else ""
            add(label, page + "?player={v}", n, f"{slug}--{first}" if first else slug,
                f"{teams[0] if teams else ''} · {years(p.get('seasons') or [])}".strip(" ·"))


# ── US sports ────────────────────────────────────────────────────────────────
def build_us():
    for p in load_json(f"{DATA}/nfl/players.json") or []:
        add("NFL", "nfl-player.html?player={v}", (p.get("name") or "").lstrip("'"), p.get("player_id"),
            years(p.get("seasons") or []))
    for p in load_json(f"{DATA}/nhl/players.json") or []:
        add("NHL", "nhl-player.html?player={v}", p.get("name"), p.get("id"),
            f"{'/'.join((p.get('teams') or [])[:2])} · {years(p.get('seasons') or [])}".strip(" ·"))
    nba = fetch_json(f"{R2}/basketball/players/index.json") or []
    for p in nba:
        add("NBA", "nba-player.html?id={v}", p.get("name"), p.get("id"), p.get("last_team") or "")
    mlb = fetch_json(f"{R2}/baseball/players.json") or load_json(f"{DATA}/baseball/players.json") or []
    for p in mlb:
        add("Baseball", "baseball-player.html?player={v}", p.get("name"))


# ── Combat / individual sports ───────────────────────────────────────────────
def build_individual():
    for p in load_json(f"{DATA}/ufc/fighters.json") or []:
        add("UFC", "ufc-fighter.html?id={v}", p.get("name"), p.get("id"), p.get("weight_class") or "")
    for n in load_json(f"{DATA}/tennis/players.json") or []:
        add("Tennis", "tennis-player.html?player={v}", n if isinstance(n, str) else n.get("name"))
    golfers = defaultdict(set)
    for r in load_json(f"{DATA}/golf/pga_winners.json") or []:
        if r.get("winner"):
            golfers[r["winner"]].add(r.get("year"))
    for n, ys in golfers.items():
        add("Golf", "golf-player.html?player={v}", n, None, years(ys))
    cyc = defaultdict(set)
    for r in load_json(f"{DATA}/cycling/riders.json") or []:
        n = re.sub(r"\[.*?\]|\(.*?\)", "", r.get("Name") or "").strip()
        if n:
            cyc[n].add(r.get("Year"))
    for n, ys in cyc.items():
        slug = unicodedata.normalize("NFD", n.lower())
        slug = re.sub(r"[̀-ͯ]", "", slug)
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        add("Cycling", "cycling-rider.html?name={v}", n, slug, years(ys))
    oly = defaultdict(set)
    for r in load_json(f"{DATA}/olympics/summer_olympic_medals.json") or []:
        if r.get("athlete"):
            oly[r["athlete"]].add(r.get("country") or "")
    for n, cs in oly.items():
        add("Olympics", "olympics-athlete.html?name={v}", n, None, "/".join(sorted(c for c in cs if c))[:40])


# ── Motorsport ───────────────────────────────────────────────────────────────
def build_motor():
    f1 = defaultdict(set)
    for path in glob.glob(f"{DATA}/f1/*.json"):
        d = load_json(path) or {}
        for race in (d.get("races") or []) if isinstance(d, dict) else []:
            for r in race.get("results") or []:
                n = re.sub(r"\s[A-Z]{3}$", "", str(r.get("driver") or "")).strip()
                if n:
                    f1[n].add(d.get("season"))
    for n, ys in f1.items():
        add("Formula 1", "f1-driver.html?driver={v}", n, None, years(ys))
    for p in load_json(f"{DATA}/nascar/drivers.json") or []:
        n = p.get("name")
        add("NASCAR", "nascar-driver.html?driver={v}", n, simple_slug(n),
            years([r.get("year") for r in p.get("races") or []]))
    for p in load_json(f"{DATA}/supercars/drivers.json") or []:
        n = p.get("name")
        add("Supercars", "supercars-driver.html?driver={v}", n, simple_slug(n),
            years([r.get("year") for r in p.get("races") or []]))
    bat = defaultdict(set)
    for path in glob.glob(f"{DATA}/bathurst/seasons/*.json"):
        d = load_json(path) or {}
        for r in d.get("results") or []:
            for n in str(r.get("driver") or "").split("/"):
                if n.strip():
                    bat[n.strip()].add(d.get("year"))
    for n, ys in bat.items():
        add("Bathurst", "bathurst-driver.html?driver={v}", n, simple_slug(n), years(ys))


# ── Cricket ──────────────────────────────────────────────────────────────────
def build_cricket():
    # short scorecard name ("AJ Finch") -> full name ("Aaron Finch"); pages
    # take the short name, so link with it and display the full one
    for label, path, page in [
        ("BBL", f"{DATA}/bbl/player-names.json", "bbl-player.html"),
        ("T20 World Cup", f"{DATA}/t20-world-cup/matches/player-names.json", "t20-world-cup-player.html"),
        ("Women's T20 World Cup", f"{DATA}/womens-t20-world-cup/matches/player-names.json",
         "womens-t20-world-cup-player.html"),
    ]:
        d = load_json(path) or {}
        for short, full in d.items():
            add(label, page + "?player={v}", full or short, short)
    for slug, full in (load_json(f"{DATA}/ipl/player-names.json") or {}).items():
        add("IPL", "ipl-player.html?player={v}", full, slug)


# ── Racing: jockeys, trainers, horses ────────────────────────────────────────
def iso_date(d):
    """'4/10/1997' -> '1997-10-04'; '1865' -> '1865'."""
    d = (d or "").strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", d)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", d)
    if m:
        return m.group(0)
    m = re.search(r"(\d{4})", d)
    return m.group(1) if m else d


def build_racing():
    """Jockeys, trainers and horses for the search index, plus per-person
    results files that the homepage search reads to show a jockey's or
    trainer's summary inline (no separate page):
        docs/data/search/racing/jockey_<letter>.json
        docs/data/search/racing/trainer_<letter>.json
    each {name: [[date, track, race, grade, horse, finish, starters, sp, partner], ...]}
    """
    horses = {}
    races = {}   # (date, race, horse) -> row  (same race can be in two files)
    files = [
        # path, cols: track, date, race, finish, starters, horse, sp, grade, jockey, trainer, horse page
        (f"{DATA}/australia-g1s.csv",
         ("VENUE", "DATE", "RACE", "FINISH", "RUNNERS", "HORSE", "SP", None, "JOCKEY", "TRAINER"),
         "australia-g1s-horse.html", "G1"),
        (f"{DATA}/Stakes races.csv",
         ("Track", "Date", "Race Name", "Position", "Starters", "Horse", "SP", "GRADE", "Jockey", "Trainer"),
         "australia-stakes-horse.html", ""),
        (f"{DATA}/australia-stakes.csv",
         ("Track", "Date", "Race", None, None, "Winner", "SP", "Race Grade", "Jockey", "Trainer"),
         "australia-stakes-winners-horse.html", ""),
    ]
    for path, cols, horse_page, default_grade in files:
        tc, dc, rc, fc, sc, hc, spc, gc, jc, trc = cols
        for r in read_csv(path):
            h = r.get(hc, "")
            if h and h.lower() not in horses:
                horses[h.lower()] = (h, horse_page)
            date = iso_date(r.get(dc))
            race = (r.get(rc) or "").strip()
            key = (date, race.lower(), h.lower())
            if key in races:
                continue
            fin = r.get(fc, "") if fc else "1"   # australia-stakes.csv is winners only
            if race.isupper():
                race = race.title()
                # keep Roman numerals and initials as capitals ("King Charles III Stakes")
                race = re.sub(r"\b(Ii|Iii|Iv|Vi|Vii|Viii|Ix|Xi|Xii)\b", lambda m: m.group(1).upper(), race)
                race = re.sub(r"\b([A-Z])\.([a-z])\b", lambda m: f"{m.group(1)}.{m.group(2).upper()}", race)
            races[key] = [date, (r.get(tc) or "").title(), race,
                          (r.get(gc) or default_grade).strip() if gc else default_grade,
                          h, fin.strip(), (r.get(sc) or "").strip() if sc else "",
                          (r.get(spc) or "").strip(), (r.get(jc) or "").strip(), (r.get(trc) or "").strip()]

    # Worldwide Group & Listed winners (USA, England, France, Japan, Ireland,
    # Germany, Hong Kong, UAE ...). Winners only, year only, no Australian
    # races in it -- so nothing double-counts with the Australian files above.
    COUNTRY_FIX = {"republic of ireland": "Ireland", "korea": "South Korea"}
    for r in read_csv(f"{DATA}/worldwide_stakes_races.csv"):
        country = (r.get("COUNTRY") or "").strip()
        country = COUNTRY_FIX.get(country.lower(), country)
        race = (r.get("RACE NAME") or "").strip()
        h = (r.get("WINNER") or "").strip()
        year = (r.get("YEAR") or "").strip()
        key = (year, race.lower(), h.lower(), country)
        if not h or key in races:
            continue
        # "HK G1" / "JPN G1" -> "G1" so Group 1 counts include them
        grade = re.sub(r"^(HK|JPN)\s+", "", (r.get("RACE GRADE") or "").strip(), flags=re.I)
        races[key] = [year, (r.get("COURSE") or "").strip(), race, grade, h, "1", "", "",
                      (r.get("JOCKEY") or "").strip(), (r.get("TRAINER") or "").strip(), country]

    by_person = {"jockey": defaultdict(list), "trainer": defaultdict(list)}
    for row in races.values():
        date, track, race, grade, horse, fin, starters, sp, jockey, trainer = row[:10]
        country = row[10] if len(row) > 10 else ""   # "" = Australia
        if jockey:
            by_person["jockey"][jockey].append([date, track, race, grade, horse, fin, starters, sp, trainer, country])
        if trainer:
            by_person["trainer"][trainer].append([date, track, race, grade, horse, fin, starters, sp, jockey, country])

    os.makedirs(f"{OUT}/racing", exist_ok=True)
    for kind, people in by_person.items():
        shards = defaultdict(dict)
        for name, rows in people.items():
            rows.sort(key=lambda x: x[0], reverse=True)
            t = norm_token(name)
            shards[t[0] if t and "a" <= t[0] <= "z" else "0"][name] = rows
            wins = sum(1 for x in rows if x[5] == "1")
            g1 = sum(1 for x in rows if x[5] == "1" and re.match(r"^g(roup)?\s*1$", x[3].strip(), re.I))
            countries = sorted({x[9] or "Australia" for x in rows},
                               key=lambda c: -sum(1 for x in rows if (x[9] or "Australia") == c))
            where = ", ".join(countries[:2]) + (f" +{len(countries) - 2}" if len(countries) > 2 else "")
            label = "Jockey" if kind == "jockey" else "Trainer"
            # "inline:" = no separate page; the homepage search shows this
            # jockey/trainer's summary right under the search box
            add(label, f"inline:{kind}", name, None,
                f"{wins:,} stakes win{'s' if wins != 1 else ''} · {g1:,} G1 · {where}")
        for L, d in shards.items():
            with open(f"{OUT}/racing/{kind}_{L}.json", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, separators=(",", ":"))

    for h, page in horses.values():
        add("Horse", page + "?horse={v}", h)


# ── WRITE SHARDS ─────────────────────────────────────────────────────────────
def norm_token(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9]", "", t)


def main():
    if not os.path.isdir(DATA):
        sys.exit("Run from the repo root (docs/data not found).")
    for step in (build_afl, build_nrl, build_soccer, build_us, build_individual,
                 build_motor, build_cricket, build_racing):
        print(f"→ {step.__name__}")
        try:
            step()
        except Exception as e:
            print(f"  ⚠ {step.__name__} failed: {e}")

    if len(PEOPLE) < 1000:
        sys.exit(f"Only {len(PEOPLE)} people found — something is wrong, not writing a broken index.")

    shards = defaultdict(list)
    for entry in PEOPLE.values():
        letters = set()
        for tok in re.split(r"[\s\-\.'’/()]+", entry[0]):
            t = norm_token(tok)
            if t:
                letters.add(t[0] if "a" <= t[0] <= "z" else "0")
        for L in letters:
            shards[L].append(entry)

    os.makedirs(OUT, exist_ok=True)
    total_bytes = 0
    for L in "abcdefghijklmnopqrstuvwxyz0":
        rows = sorted(shards.get(L, []), key=lambda e: (e[0].lower(), e[1]))
        payload = {"src": SOURCES, "p": rows}
        path = f"{OUT}/people_{L}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        total_bytes += os.path.getsize(path)

    meta = {"total": len(PEOPLE), "by_sport": dict(sorted(COUNTS.items()))}
    with open(f"{OUT}/meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    print("\nPeople per sport:")
    for k, v in sorted(COUNTS.items(), key=lambda x: -x[1]):
        print(f"  {k:24} {v:>7,}")
    print(f"TOTAL {len(PEOPLE):,} people · {total_bytes/1e6:.1f} MB across 27 shards")


if __name__ == "__main__":
    main()
