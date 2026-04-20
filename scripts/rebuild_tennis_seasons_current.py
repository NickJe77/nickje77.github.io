import json
import os
from collections import defaultdict

OUT = "docs/data/tennis/seasons"

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def build(year):

    tournaments = {
        "Australian Open": [],
        "Adelaide": [],
        "Acapulco": []
    }

    # generate matches across tournaments
    for i in range(1, 31):

        if i <= 10:
            t = "Adelaide"
        elif i <= 20:
            t = "Australian Open"
        else:
            t = "Acapulco"

        tournaments[t].append({
            "date": f"{year}-01-{str(i%28+1).zfill(2)}",
            "player1": f"Player {i}",
            "player2": f"Player {i+1}",
            "score": "6-4 6-3"
        })

    output = []

    for name, matches in tournaments.items():

        dates = sorted([m["date"] for m in matches])

        output.append({
            "tournament": name,
            "surface": "Hard",
            "location": "",
            "tour": "ATP",
            "start_date": dates[0],
            "end_date": dates[-1],
            "date": dates[0],
            "matches": matches
        })

    output.sort(key=lambda x: x["date"])

    return output


def main():

    save(f"{OUT}/2025.json", build("2025"))
    save(f"{OUT}/2026.json", build("2026"))

    print("✅ MULTI TOURNAMENT DATA CREATED")


if __name__ == "__main__":
    main()
