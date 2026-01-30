#!/usr/bin/env python3
"""
Builds docs/data/on_this_day.json from existing sport datasets.

Sources:
- NBA:     docs/data/nba/nba_season_*.json
- F1:      docs/data/f1/*.json
- AFL:     docs/data/afl/*.json
- Racing:  docs/data/racing/*.json

Output:
- docs/data/on_this_day.json
"""

import os
import json
from collections import defaultdict
from datetime import datetime

OUT_FILE = "docs/data/on_this_day.json"

NBA_DIR = "docs/data/nba"
F1_DIR = "docs/data/f1"
AFL_DIR = "docs/data/afl"
RACING_DIR = "docs/data/racing"

on_this_day = defaultdict(lambda: defaultdict(list))

# -----------------------
# Helpers
# -----------------------

def parse_date(date_str):
    if not date_str:
        return None

    date_str = date_str.strip()

    fmts = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y-%m-%dT%H:%M:%S"
    ]

    for f in fmts:
        try:
            return datetime.strptime(date_str[:19], f)
        except:
            pass
    return None

def add_event(dt, sport, text):
    mm_dd = dt.strftime("%m-%d")
    on_this_day[mm_dd][sport].append({
        "year": dt.year,
        "text": text
    })

def safe_load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def extract_list(data, *keys):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            if k in data and isinstance(data[k], list):
                return data[k]
    return []

# -----------------------
# NBA
# -----------------------

if os.path.exists(NBA_DIR):
    for fname in os.listdir(NBA_DIR):
        if not fname.startswith("nba_season_"):
            continue

        path = os.path.join(NBA_DIR, fname)
        data = safe_load(path)
        if not data:
            continue

        games = extract_list(data, "games")
        for g in games:
            dt = parse_date(g.get("date",""))
            if not dt:
                continue

            text = f"{g.get('home_team','')} def {g.get('away_team','')} {g.get('home_points',0)}–{g.get('away_points',0)}"
            add_event(dt, "NBA", text)

# -----------------------
# F1
# -----------------------

if os.path.exists(F1_DIR):
    for fname in os.listdir(F1_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(F1_DIR, fname)
        data = safe_load(path)
        if not data:
            continue

        races = extract_list(data, "races", "results")
        for r in races:
            dt = parse_date(r.get("date",""))
            if not dt:
                continue

            race = r.get("race", r.get("grand_prix", "Grand Prix"))
            winner = r.get("winner", "")
            text = f"{winner} wins the {race}"
            add_event(dt, "F1", text)

# -----------------------
# AFL
# -----------------------

if os.path.exists(AFL_DIR):
    for fname in os.listdir(AFL_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(AFL_DIR, fname)
        data = safe_load(path)
        if not data:
            continue

        games = extract_list(data, "games")
        for g in games:
            dt = parse_date(g.get("date",""))
            if not dt:
                continue

            home = g.get("home_team","")
            away = g.get("away_team","")
            hp = g.get("home_points",0)
            ap = g.get("away_points",0)
            venue = g.get("venue","")

            text = f"{home} def {away} {hp}–{ap}"
            if venue:
                text += f" ({venue})"

            add_event(dt, "AFL", text)

# -----------------------
# Racing
# -----------------------

if os.path.exists(RACING_DIR):
    for fname in os.listdir(RACING_DIR):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(RACING_DIR, fname)
        data = safe_load(path)
        if not data:
            continue

        races = extract_list(data, "races", "results")
        for r in races:
            dt = parse_date(r.get("date",""))
            if not dt:
                continue

            race = r.get("race","Group 1 Race")
            winner = r.get("winner","")
            text = f"{winner} wins the {race}"
            add_event(dt, "Racing", text)

# -----------------------
# Sort
# -----------------------

for mmdd in on_this_day:
    for sport in on_this_day[mmdd]:
        on_this_day[mmdd][sport] = sorted(
            on_this_day[mmdd][sport],
            key=lambda x: x["year"]
        )

os.makedirs("docs/data", exist_ok=True)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(on_this_day, f, indent=2)

print("Built:", OUT_FILE)