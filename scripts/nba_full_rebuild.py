import os
import json

BASE_DIR = "docs/data/nba"

print("RECOVERING NBA games.json FILES")

for season in os.listdir(BASE_DIR):

    season_dir = os.path.join(BASE_DIR, season)

    if not os.path.isdir(season_dir):
        continue

    print(f"PROCESSING {season}")

    games = []

    for filename in os.listdir(season_dir):

        if not filename.endswith(".json"):
            continue

        if filename in ["games.json", "index.json"]:
            continue

        path = os.path.join(season_dir, filename)

        try:

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

        except Exception:
            continue

        # ====================================
        # HANDLE ARRAY FILES
        # ====================================

        if isinstance(data, list):

            for g in data:

                if not isinstance(g, dict):
                    continue

                # MUST LOOK LIKE A GAME
                if (
                    g.get("home_team")
                    or g.get("away_team")
                    or g.get("players")
                ):
                    games.append(g)

            continue

        # ====================================
        # HANDLE SINGLE GAME FILES
        # ====================================

        if isinstance(data, dict):

            if (
                data.get("home_team")
                or data.get("away_team")
                or data.get("players")
            ):
                games.append(data)

    # ====================================
    # REMOVE DUPLICATES
    # ====================================

    seen = set()
    cleaned = []

    for g in games:

        gid = str(g.get("game_id", ""))

        if gid and gid in seen:
            continue

        if gid:
            seen.add(gid)

        cleaned.append(g)

    # ====================================
    # SORT IF POSSIBLE
    # ====================================

    try:

        cleaned.sort(
            key=lambda x: x.get("date", "")
        )

    except:
        pass

    out_path = os.path.join(
        season_dir,
        "games.json"
    )

    with open(
        out_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            cleaned,
            f,
            indent=2
        )

    print(f"{season} -> {len(cleaned)} games")

print("DONE")
