import json
from pathlib import Path

print("🏆 Building Davis Cup TIE dataset")

IN = Path("docs/data/tennis/davis_cup/2025.json")
OUT = Path("docs/data/tennis/davis_cup/2025_ties.json")

with open(IN) as f:
    matches = json.load(f)

ties = {}

# -------------------------
# GROUP MATCHES BY TIE
# -------------------------
for m in matches:
    key = (m["date"][:4], m["tie"], m["round"])  # year + tie + round

    if key not in ties:
        ties[key] = {
            "year": m["date"][:4],
            "tie": m["tie"],
            "round": m["round"],
            "matches": [],
            "team1_wins": 0,
            "team2_wins": 0
        }

    ties[key]["matches"].append(m)

# -------------------------
# CALCULATE WINNERS
# -------------------------
for key, tie in ties.items():
    team1, team2 = tie["tie"].split(" vs ")

    for m in tie["matches"]:
        score = m["score"]

        if not score:
            continue

        sets = score.split()

        p1_sets = 0
        p2_sets = 0

        for s in sets:
            if "-" not in s:
                continue
            a, b = s.split("-")
            if int(a) > int(b):
                p1_sets += 1
            else:
                p2_sets += 1

        if p1_sets > p2_sets:
            tie["team1_wins"] += 1
        else:
            tie["team2_wins"] += 1

    # determine winner
    if tie["team1_wins"] > tie["team2_wins"]:
        tie["winner"] = team1
    else:
        tie["winner"] = team2

    tie["score"] = f"{tie['team1_wins']}-{tie['team2_wins']}"

# -------------------------
# FINAL STRUCTURE
# -------------------------
output = {}

for key, tie in ties.items():
    year = tie["year"]

    if year not in output:
        output[year] = []

    output[year].append({
        "tie": tie["tie"],
        "round": tie["round"],
        "winner": tie["winner"],
        "score": tie["score"],
        "matches": tie["matches"]
    })

with open(OUT, "w") as f:
    json.dump(output, f, indent=2)

print("✅ Built ties:", sum(len(v) for v in output.values()))
