def build_players(rows):

    if PLAYERS_DIR.exists():
        shutil.rmtree(PLAYERS_DIR)

    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)

    players = {}

    print("Grouping players...")

    for r in rows:
        name = clean(r.get("player"))
        if not name:
            continue

        slug = slugify(name)

        if slug not in players:
            players[slug] = []

        players[slug].append(r)

    print("Total players:", len(players))

    index = []

    print("Building + writing players...")

    batch = []
    BATCH_SIZE = 50  # 🔥 critical

    for i, (slug, games_raw) in enumerate(players.items()):

        seen = set()
        games = []

        for r in games_raw:
            key = (
                r.get("season"),
                r.get("round"),
                r.get("played_for"),
                r.get("played_against"),
                r.get("K"), r.get("HB"), r.get("D")
            )

            if key in seen:
                continue

            seen.add(key)

            games.append({
                "season": r.get("season"),
                "round": r.get("round"),
                "team": r.get("played_for"),
                "opponent": r.get("played_against"),
                "K": to_int(r.get("K")),
                "HB": to_int(r.get("HB")),
                "D": to_int(r.get("D")),
                "M": to_int(r.get("M")),
                "G": to_int(r.get("G")),
                "B": to_int(r.get("B")),
                "T": to_int(r.get("T")),
                "HO": to_int(r.get("HO")),
                "GA": to_int(r.get("GA")),
                "I50": to_int(r.get("I50")),
                "CL": to_int(r.get("CL")),
                "CG": to_int(r.get("CG")),
                "R50": to_int(r.get("R50")),
                "FF": to_int(r.get("FF")),
                "FA": to_int(r.get("FA")),
                "AF": to_int(r.get("AF")),
                "SC": to_int(r.get("SC"))
            })

        games.sort(key=lambda g: (g["season"], g["round"] or 999))

        player_name = clean(games_raw[0].get("player"))

        seasons = sorted({g["season"] for g in games})
        teams = list(dict.fromkeys([g["team"] for g in games]))

        out = {
            "player": player_name,
            "slug": slug,
            "seasons": seasons,
            "teams": teams,
            "games": games
        }

        batch.append((slug, out))

        # 🔥 WRITE IN BATCHES
        if len(batch) >= BATCH_SIZE:
            for s, data in batch:
                with open(PLAYERS_DIR / f"{s}.json", "w") as f:
                    json.dump(data, f)

            batch = []

        index.append({
            "player": player_name,
            "slug": slug,
            "seasons": seasons,
            "teams": teams
        })

        if i % 100 == 0:
            print(f"Processed {i} players")

    # 🔥 write remaining
    for s, data in batch:
        with open(PLAYERS_DIR / f"{s}.json", "w") as f:
            json.dump(data, f)

    print("Writing index...")

    with open(PLAYERS_INDEX, "w") as f:
        json.dump(index, f)

    print("DONE")
