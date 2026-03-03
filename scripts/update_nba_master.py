def main():
    # Hard start date (your last saved game)
    start_date = date(2025, 2, 15)

    today = date.today()
    written = 0

    day = start_date

    while day <= today:
        url = SCOREBOARD_URL.format(date=day.strftime("%Y%m%d"))

        try:
            scoreboard = get_json(url)
        except:
            day += timedelta(days=1)
            continue

        games = scoreboard.get("scoreboard", {}).get("games", [])

        for g in games:
            if g.get("gameStatus") != 3:
                continue

            game_id = g["gameId"]
            filename = filename_from_gameid(game_id)
            path = OUT_DIR / filename

            if path.exists():
                continue

            try:
                time.sleep(0.4)
                box = get_json(BOXSCORE_URL.format(gameId=game_id))
                game_data = build_game(box)

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(game_data, f, indent=2)

                print("Created:", filename)
                written += 1

            except Exception as e:
                print("Failed:", game_id, e)

        day += timedelta(days=1)

    print("Done. New games written:", written)
