import json
from pathlib import Path
from collections import defaultdict

print("BUILDING IPL SCORECARDS FROM FULL DATA")

INPUT_FILE = Path("docs/data/ipl/ipl_2025_FULL.json")  # change year if needed
OUTPUT_DIR = Path("docs/data/ipl/boxscores")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_scorecard(match):
    teams = match["info"]["teams"]
    venue = match["info"].get("venue", "")
    result = match["info"].get("outcome", {})

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
            "overs": 0,
            "runs": 0,
            "wickets": 0,
            "balls": 0
        })

        # -------------------------
        # PROCESS BALL DATA
        # -------------------------
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

        # -------------------------
        # FORMAT BATTING
        # -------------------------
        batting_list = []
        for player, stats in batting.items():
            balls = stats["balls"]
            sr = round((stats["runs"] / balls) * 100, 2) if balls else 0

            batting_list.append({
                "player": player,
                "runs": stats["runs"],
                "balls": balls,
                "4s": stats["4s"],
                "6s": stats["6s"],
                "sr": sr
            })

        # -------------------------
        # FORMAT BOWLING
        # -------------------------
        bowling_list = []
        for bowler, stats in bowling.items():
            overs = round(stats["balls"] / 6, 1)
            econ = round(stats["runs"] / overs, 2) if overs else 0

            bowling_list.append({
                "bowler": bowler,
                "overs": overs,
                "runs": stats["runs"],
                "wickets": stats["wickets"],
                "econ": econ
            })

        innings_out.append({
            "team": team,
            "batting": batting_list,
            "bowling": bowling_list
        })

    return {
        "teams": teams,
        "venue": venue,
        "result": result,
        "innings": innings_out
    }


def main():
    with open(INPUT_FILE) as f:
        data = json.load(f)

    matches = data if isinstance(data, list) else [data]

    for i, match in enumerate(matches):
        game_id = f"ipl_{i+1}"

        scorecard = build_scorecard(match)

        out_file = OUTPUT_DIR / f"{game_id}.json"
        with open(out_file, "w") as f:
            json.dump(scorecard, f, indent=2)

        print("Saved:", game_id)


if __name__ == "__main__":
    main()
