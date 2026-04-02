import json
from pathlib import Path
from collections import defaultdict

print("BUILDING IPL 2026 SEASON FILE (CORRECT STRUCTURE)")

INPUT_FILE = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT_FILE = Path("docs/data/ipl/ipl_2026.json")

if not INPUT_FILE.exists():
    print("❌ ipl_2026_FULL.json NOT FOUND")
    exit()


def build_match(match, idx):
    info = match["info"]

    teams = info.get("teams", [])
    venue = info.get("venue", "")
    date = info.get("dates", [""])[0]

    result = info.get("outcome", {})
    winner = result.get("winner", "")
    margin = ""

    if "by" in result:
        if "runs" in result["by"]:
            margin = f"{result['by']['runs']} runs"
        elif "wickets" in result["by"]:
            margin = f"{result['by']['wickets']} wickets"

    innings_out = []

    for inn in match["innings"]:
        team = inn["team"]

        batting = defaultdict(lambda: {
            "runs": 0,
            "balls": 0,
            "4s": 0,
            "6s": 0
        })

        bowling = defaultdict(lambda: {
            "balls": 0,
            "runs": 0,
            "wickets": 0
        })

        for over in inn["overs"]:
            for d in over["deliveries"]:
                batter = d["batter"]
                bowler = d["bowler"]

                runs = d["runs"]["batter"]
                total = d["runs"]["total"]

                batting[batter]["runs"] += runs
                batting[batter]["balls"] += 1

                if runs == 4:
                    batting[batter]["4s"] += 1
                if runs == 6:
                    batting[batter]["6s"] += 1

                bowling[bowler]["runs"] += total
                bowling[bowler]["balls"] += 1

                if "wickets" in d:
                    bowling[bowler]["wickets"] += len(d["wickets"])

        # format batting
        batting_list = []
        for p, s in batting.items():
            balls = s["balls"]
            sr = round((s["runs"] / balls) * 100, 2) if balls else 0

            batting_list.append({
                "player": p,
                "runs": s["runs"],
                "balls": balls,
                "4s": s["4s"],
                "6s": s["6s"],
                "sr": sr
            })

        # format bowling
        bowling_list = []
        for b, s in bowling.items():
            overs = s["balls"] // 6 + (s["balls"] % 6) / 10
            econ = round(s["runs"] / (s["balls"] / 6), 2) if s["balls"] else 0

            bowling_list.append({
                "bowler": b,
                "overs": overs,
                "runs": s["runs"],
                "wickets": s["wickets"],
                "econ": econ
            })

        innings_out.append({
            "team": team,
            "batting": batting_list,
            "bowling": bowling_list
        })

    return {
        "game_id": f"ipl_2026_{idx}",
        "date": date,
        "teams": teams,
        "venue": venue,
        "winner": winner,
        "margin": margin,
        "innings": innings_out
    }


def main():
    with open(INPUT_FILE) as f:
        data = json.load(f)

    matches = data if isinstance(data, list) else [data]

    output = {
        "season": 2026,
        "matches": []
    }

    for i, match in enumerate(matches, 1):
        built = build_match(match, i)
        output["matches"].append(built)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
