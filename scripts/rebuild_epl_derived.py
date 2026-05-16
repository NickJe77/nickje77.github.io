# =================================================
# REDS
# =================================================

red_seen = set()

# PLAYERS WHO NEVER RECEIVED EPL REDS
ZERO_RED_PLAYERS = {
    "Freddie Ljungberg",
    "Thierry Henry",
    "Robert Pirès"
}

for red in game["red_cards"]:

    if not isinstance(red, dict):
        continue

    player = fix_name(
        red.get("player")
    )

    team = clean(
        red.get("team")
    )

    minute = clean(
        red.get("minute")
    )

    if not player or not team:
        continue

    # =============================================
    # FORCE KNOWN ZERO RED PLAYERS
    # =============================================

    if player in ZERO_RED_PLAYERS:
        continue

    red_key = (
        f"{match_key}|"
        f"{player.lower()}|"
        f"{team.lower()}|"
        f"{minute}"
    )

    if red_key in red_seen:
        continue

    red_seen.add(red_key)

    slug = slugify(player)

    if slug not in players:

        players[slug] = {
            "player": player,
            "slug": slug,
            "goals": 0,
            "yellow_cards": 0,
            "red_cards": 0
        }

    players[slug]["red_cards"] += 1

    team_reds[team][player] += 1
