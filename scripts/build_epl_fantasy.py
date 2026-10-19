"""
build_epl_fantasy.py

Adds official Fantasy Premier League (FPL) points to the EPL pages.

Source: the official FPL per-gameweek data, archived season by season at
github.com/vaastav/Fantasy-Premier-League (data/<season>/gws/merged_gw.csv),
available from 2016-17 onwards. FPL scoring needs minutes, assists, clean
sheets, saves and bonus points, which the site's fbref data doesn't have,
so the official points are used rather than calculated.

Matching, per season:
  1. FPL rows are grouped into fixtures (fixture id + home/away side).
  2. Each FPL fixture is matched to the site's game on the same date (+/- 1
     day, FPL kickoffs are UTC) whose lineups share the most players. This
     needs no team-name mapping, which early FPL seasons don't even have.
  3. Each FPL player is matched to the fbref lineup name on their side
     (exact, then name-contained, then surname + initial), so links and the
     player page use the site's own names.

Run from the repo root (the GitHub Action does this):
    python scripts/build_epl_fantasy.py            # all seasons 2016-17 ->
    python scripts/build_epl_fantasy.py 2025-26    # one season

Writes:
    docs/data/epl/fantasy/<YYYY-YYYY>.json  {match_id: {"home": [[name, pts, mins], ...], "away": [...]}}
    docs/data/epl/fantasy/players.json      {name: {season: [pts, games, best_pts, best_vs, best_date]}}
"""

import csv
import io
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta

import requests

DATA = "docs/data/epl"
OUT = f"{DATA}/fantasy"
FPL_URL = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{s}/gws/merged_gw.csv"
FIRST = 2016


# letters NFKD can't split into a base letter + accent
SPECIAL = str.maketrans({"ð": "d", "Ð": "D", "ø": "o", "Ø": "O", "ı": "i", "ł": "l", "Ł": "L",
                         "æ": "ae", "Æ": "AE", "ß": "ss", "đ": "d", "Đ": "D", "þ": "th", "œ": "oe"})


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "").translate(SPECIAL)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s.replace("-", " ")).split()


def fpl_name(raw):
    # old seasons: "Aaron_Cresswell" or "Aaron_Cresswell_402"
    return re.sub(r"_\d+$", "", raw or "").replace("_", " ").strip()


def lineup_names(match, side):
    out = []
    for p in match.get(f"{side}_lineup") or []:
        n = p.get("name") if isinstance(p, dict) else p
        if n:
            out.append(n)
    return out


def match_name(fpl, candidates, web_name=None):
    """Return the fbref name on this side that is this FPL player, or None.
    web_name = FPL's short display name ("Paquetá", "Casemiro", "Jota"),
    used when FPL lists a full legal name."""
    ft = norm(fpl)
    if not ft:
        return None
    fs = set(ft)
    # 1. exact (also ignoring spaces: "Kim Ji-soo" = "Kim Jisoo")
    for c in candidates:
        if norm(c) == ft or "".join(norm(c)) == "".join(ft):
            return c
    # 2. one name's words are all inside the other ("Bruno Fernandes" in
    #    "Bruno Borges Fernandes", "Jaden Philogene" in "Jaden Philogene Bidace")
    hits = [c for c in candidates if norm(c) and (set(norm(c)) <= fs or fs <= set(norm(c)))]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:   # prefer the longest (most specific) one
        hits.sort(key=lambda c: -len(norm(c)))
        if len(norm(hits[0])) > len(norm(hits[1])):
            return hits[0]
    # 2b. FPL short name: "Paquetá" -> "Lucas Paquetá", "Casemiro" -> "Casemiro"
    if web_name:
        # "L.Paquetá" -> initial "l" + "paqueta"
        parts = norm(web_name)
        initials = [t for t in parts if len(t) == 1]
        wt = [t for t in parts if len(t) > 1]
        if wt:
            hits = [c for c in candidates if norm(c) and set(wt) <= set(norm(c))
                    and all(any(x.startswith(i) for x in norm(c)) for i in initials)]
            if len(hits) == 1:
                return hits[0]
    # 3. same surname and first initial
    hits = [c for c in candidates if norm(c) and norm(c)[-1] == ft[-1] and norm(c)[0][0] == ft[0][0]]
    if len(hits) == 1:
        return hits[0]
    # 4. fbref surname appears in the FPL name, and only one such player
    hits = [c for c in candidates if norm(c) and norm(c)[-1] in fs and len(norm(c)[-1]) > 2]
    if len(hits) == 1:
        return hits[0]
    return None


def season_pairs(only=None):
    today = date.today()
    last = today.year if today.month >= 7 else today.year - 1
    pairs = [(f"{y}-{str(y + 1)[2:]}", f"{y}-{y + 1}") for y in range(FIRST, last + 1)]
    if only:
        pairs = [p for p in pairs if only in p]
    return pairs


def decode(raw):
    # recent files are UTF-8; early ones (2016-17 ...) are Latin-1/cp1252
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def load_fpl(fpl_season):
    r = requests.get(FPL_URL.format(s=fpl_season), timeout=120)
    if r.status_code != 200:
        print(f"  no FPL data for {fpl_season} (HTTP {r.status_code})")
        return []
    return list(csv.DictReader(io.StringIO(decode(r.content))))


def load_web_names(fpl_season):
    """element id -> FPL short display name, from that season's players_raw.csv."""
    url = FPL_URL.format(s=fpl_season).replace("gws/merged_gw.csv", "players_raw.csv")
    try:
        r = requests.get(url, timeout=120)
        if r.status_code != 200:
            return {}
        return {row.get("id"): row.get("web_name") for row in csv.DictReader(io.StringIO(decode(r.content)))}
    except Exception:
        return {}


def build_season(fpl_season, site_season, players_out):
    season_file = f"{DATA}/seasons/{site_season}.json"
    if not os.path.exists(season_file):
        print(f"  [{site_season}] no site season file, skipping")
        return
    games = json.load(open(season_file, encoding="utf-8")).get("games", [])
    rows = load_fpl(fpl_season)
    if not rows:
        return
    web = load_web_names(fpl_season)

    # site games by date, with their lineups
    by_date = defaultdict(list)
    for g in games:
        path = f"{DATA}/matches/{site_season}/{g['match_id']}.json"
        if not os.path.exists(path):
            continue
        try:
            m = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        g = dict(g, _home=lineup_names(m, "home"), _away=lineup_names(m, "away"),
                 _home_team=m.get("home_team") or g.get("home"), _away_team=m.get("away_team") or g.get("away"))
        by_date[g.get("date", "")[:10]].append(g)

    # FPL fixtures
    fixtures = defaultdict(lambda: {"home": [], "away": [], "kick": ""})
    for r in rows:
        try:
            mins = int(float(r.get("minutes") or 0))
            pts = int(float(r.get("total_points") or 0))
        except ValueError:
            continue
        if mins <= 0:
            continue
        side = "home" if str(r.get("was_home")).strip().lower() in ("true", "1") else "away"
        f = fixtures[r.get("fixture")]
        f[side].append((fpl_name(r.get("name")), pts, mins, web.get(r.get("element"))))
        f["kick"] = (r.get("kickoff_time") or "")[:10]

    out = {}
    matched_fx = unmatched_fx = 0
    named = total_players = 0
    for fx, f in fixtures.items():
        try:
            d = datetime.strptime(f["kick"], "%Y-%m-%d").date()
        except ValueError:
            unmatched_fx += 1
            continue
        cands = []
        for delta in (0, -1, 1):
            cands += by_date.get((d + timedelta(days=delta)).isoformat(), [])
        best, best_score = None, 0
        for g in cands:
            score = sum(1 for n, _, _, w in f["home"] if match_name(n, g["_home"], w)) + \
                    sum(1 for n, _, _, w in f["away"] if match_name(n, g["_away"], w))
            if score > best_score:
                best, best_score = g, score
        if not best or best_score < 4:
            unmatched_fx += 1
            continue
        matched_fx += 1
        entry = {}
        for side, opp_side in (("home", "away"), ("away", "home")):
            lst = []
            for n, pts, mins, w in sorted(f[side], key=lambda x: -x[1]):
                site_name = match_name(n, best[f"_{side}"], w)
                total_players += 1
                if site_name:
                    named += 1
                name = site_name or n
                lst.append([name, pts, mins])
                opp = best[f"_{opp_side}_team"]
                s = players_out[name].setdefault(site_season, [0, 0, None, "", ""])
                s[0] += pts
                s[1] += 1
                if s[2] is None or pts > s[2]:
                    s[2], s[3], s[4] = pts, opp, best.get("date", "")
            entry[side] = lst
        out[best["match_id"]] = entry

    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/{site_season}.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    pct = (named / total_players * 100) if total_players else 0
    print(f"  [{site_season}] {matched_fx} games matched, {unmatched_fx} FPL fixtures unmatched, "
          f"{named}/{total_players} player-games matched to site names ({pct:.1f}%)")


def main():
    if not os.path.isdir(DATA):
        sys.exit("Run from the repo root (docs/data/epl not found).")
    only = sys.argv[1] if len(sys.argv) > 1 else None
    players_path = f"{OUT}/players.json"
    players_out = defaultdict(dict)
    if only and os.path.exists(players_path):
        # one-season run: keep the other seasons already built
        for n, seasons in json.load(open(players_path, encoding="utf-8")).items():
            players_out[n].update(seasons)
        for n in players_out:
            players_out[n].pop(only.replace("-", "-20") if len(only) == 7 else only, None)
    for fpl_season, site_season in season_pairs(only):
        print(f"→ {fpl_season}")
        try:
            build_season(fpl_season, site_season, players_out)
        except Exception as e:
            print(f"  ⚠ {fpl_season} failed: {e}")
    os.makedirs(OUT, exist_ok=True)
    with open(players_path, "w", encoding="utf-8") as fh:
        json.dump(players_out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"players.json: {len(players_out):,} players")


if __name__ == "__main__":
    main()
