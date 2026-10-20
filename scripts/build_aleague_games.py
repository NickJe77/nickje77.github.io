"""
build_aleague_games.py

A-League only. Builds every player's individual games from the site's own
A-League match files, for the player page's Games Played box and game log.

Run from the repo root (the GitHub Action does this):
    python scripts/build_aleague_games.py

Writes docs/data/aleague/player_games/<first two letters>.json
    {name: [[season, match_id, date, team, opponent, home(1/0), goals_for,
             goals_against, G, YC, RC, null, minutes or null], ...]}
"""

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

DATA = "docs/data/aleague"

SPECIAL = str.maketrans({"ð": "d", "Ð": "D", "ø": "o", "Ø": "O", "ı": "i", "ł": "l", "Ł": "L",
                         "æ": "ae", "Æ": "AE", "ß": "ss", "đ": "d", "Đ": "D", "þ": "th", "œ": "oe"})


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "").translate(SPECIAL)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s.replace("-", " ")).split()


def lineup(match, side):
    out = []
    for p in match.get(f"{side}_lineup") or []:
        if isinstance(p, dict) and p.get("name"):
            out.append((p["name"], p.get("minutes")))
        elif isinstance(p, str) and p:
            out.append((p, None))
    return out


def main():
    if not os.path.isdir(f"{DATA}/seasons"):
        sys.exit("Run from the repo root (docs/data/aleague/seasons not found).")
    games_by_player = defaultdict(list)
    for season_file in sorted(os.listdir(f"{DATA}/seasons")):
        if not season_file.endswith(".json"):
            continue
        season = season_file[:-5]
        try:
            games = json.load(open(f"{DATA}/seasons/{season_file}", encoding="utf-8")).get("games", [])
        except Exception:
            continue
        for g in games:
            path = f"{DATA}/matches/{season}/{g['match_id']}.json"
            if not os.path.exists(path):
                continue
            try:
                m = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            ht, at = m.get("home_team") or g.get("home"), m.get("away_team") or g.get("away")
            hs = m.get("home_score", g.get("score_home"))
            as_ = m.get("away_score", g.get("score_away"))
            goals, yc, rc = defaultdict(int), defaultdict(int), defaultdict(int)
            for e in m.get("scorers") or []:
                if not e.get("own_goal") and e.get("player"):
                    goals[e["player"]] += 1
            for e in m.get("yellow_cards") or []:
                if e.get("player"):
                    yc[e["player"]] += 1
            for e in m.get("red_cards") or []:
                if e.get("player"):
                    rc[e["player"]] += 1
            for side in ("home", "away"):
                team, opp = (ht, at) if side == "home" else (at, ht)
                gf, ga = (hs, as_) if side == "home" else (as_, hs)
                for n, mins in lineup(m, side):
                    games_by_player[n].append([season, g["match_id"], g.get("date", ""), team, opp,
                                               1 if side == "home" else 0, gf, ga,
                                               goals[n], yc[n], rc[n], None, mins])

    shards = defaultdict(dict)
    for n, lst in games_by_player.items():
        lst.sort(key=lambda x: (x[0], x[2], x[1]), reverse=True)
        t = "".join(norm(n))[:2]
        shards[t if len(t) == 2 else "0"][n] = lst
    os.makedirs(f"{DATA}/player_games", exist_ok=True)
    for L, d in shards.items():
        with open(f"{DATA}/player_games/{L}.json", "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"A-League player_games: {len(games_by_player):,} players, "
          f"{sum(len(v) for v in games_by_player.values()):,} player-games")


if __name__ == "__main__":
    main()
