import json
from pathlib import Path

print("LIV SCRAPER (STABLE DATA BUILDER)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# HARD DATA (RELIABLE BASE)
# -----------------------------------

DATA = {
    2022: [
        ("LIV Golf London", "9–11 June", "England", "Charl Schwartzel", "-7"),
        ("LIV Golf Portland", "30 June–2 July", "USA", "Branden Grace", "-13"),
        ("LIV Golf Bedminster", "29–31 July", "USA", "Henrik Stenson", "-11"),
        ("LIV Golf Boston", "2–4 September", "USA", "Dustin Johnson", "-15"),
        ("LIV Golf Chicago", "16–18 September", "USA", "Cameron Smith", "-13"),
        ("LIV Golf Bangkok", "7–9 October", "Thailand", "Eugenio Chacarra", "-19"),
        ("LIV Golf Jeddah", "14–16 October", "Saudi Arabia", "Brooks Koepka", "-19"),
        ("LIV Golf Miami", "28–30 October", "USA", "Dustin Johnson", "-5"),
    ],

    2023: [
        ("LIV Golf Mayakoba", "24–26 Feb", "Mexico", "Charles Howell III", "-16"),
        ("LIV Golf Tucson", "17–19 Mar", "USA", "Talor Gooch", "-19"),
        ("LIV Golf Orlando", "31 Mar–2 Apr", "USA", "Brooks Koepka", "-15"),
        ("LIV Golf Adelaide", "21–23 Apr", "Australia", "Talor Gooch", "-19"),
        ("LIV Golf Singapore", "28–30 Apr", "Singapore", "Talor Gooch", "-17"),
        ("LIV Golf Tulsa", "12–14 May", "USA", "Dustin Johnson", "-9"),
        ("LIV Golf DC", "26–28 May", "USA", "Harold Varner III", "-12"),
        ("LIV Golf Andalucía", "30 Jun–2 Jul", "Spain", "Talor Gooch", "-12"),
        ("LIV Golf London", "7–9 Jul", "England", "Cameron Smith", "-15"),
        ("LIV Golf Greenbrier", "4–6 Aug", "USA", "Joaquin Niemann", "-21"),
        ("LIV Golf Bedminster", "11–13 Aug", "USA", "Cameron Smith", "-12"),
        ("LIV Golf Chicago", "15–17 Sep", "USA", "Bryson DeChambeau", "-13"),
        ("LIV Golf Jeddah", "13–15 Oct", "Saudi Arabia", "Brooks Koepka", "-16"),
        ("LIV Golf Miami", "20–22 Oct", "USA", "Team event", ""),
    ],

    2024: [],
    2025: [],
    2026: []
}


# -----------------------------------
# BUILD FILES
# -----------------------------------

all_events = []

for year, events in DATA.items():
    output = []

    for e in events:
        output.append({
            "season": year,
            "event": e[0],
            "date": e[1],
            "location": e[2],
            "winner": e[3],
            "score": e[4]
        })

    with open(OUT / f"{year}.json", "w") as f:
        json.dump(output, f, indent=2)

    all_events.extend(output)

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("DONE — STABLE DATA CREATED")
