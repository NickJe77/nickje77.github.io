import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("AFL FOOTYWIRE -> FULL FIXED SCRAPER")

YEAR = 2026
BASE = "https://www.footywire.com/afl/footy/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON_OUTPUT = Path(f"docs/data/afl/afl_{YEAR}.json")
PLAYERS_OUTPUT = Path("docs/data/afl/players.json")
SEASON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def num(value):
    value = clean(value).replace(",", "")
    try:
        return int(value)
    except Exception:
        return 0


def slug(text):
    text = clean(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def format_score(points):
    goals = points // 6
    behinds = points % 6
    return f"{goals}.{behinds} ({points})"


def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def get_match_links():
    url = f"{BASE}ft_match_list?year={YEAR}"
    print("Fetching season page:", url)

    soup = BeautifulSoup(get_html(url), "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "ft_match_statistics?mid=" in href:
            full = href if href.startswith("http") else BASE + href
            if full not in links:
                links.append(full)

    print("Matches found:", len(links))
    return links


def parse_header_info(soup):
    text_lines = [clean(x) for x in soup.get_text("\n").split("\n")]
    text_lines = [x for x in text_lines if x]

    result_line = ""
    detail_line = ""
    date_line = ""

    for i, line in enumerate(text_lines):
        if " defeats " in line or " drew " in line:
            result_line = line
            if i + 1 < len(text_lines):
                detail_line = text_lines[i + 1]
            if i + 2 < len(text_lines):
                date_line = text_lines[i + 2]
            break

    team_a = ""
    team_b = ""
    outcome = ""

    if " defeats " in result_line:
        left, right = result_line.split(" defeats ", 1)
        team_a = clean(left)
        team_b = clean(right)
        outcome = "defeats"
    elif " drew " in result_line:
        left, right = result_line.split(" drew ", 1)
        team_a = clean(left)
        team_b = clean(right)
        outcome = "drew"

    round_name = ""
    venue = ""
    crowd = ""
    date_iso = ""

    round_match = re.search(r"(Round\s+\d+|Qualifying Final|Elimination Final|Semi Final|Preliminary Final|Grand Final)", detail_line, re.I)
    if round_match:
        round_name = clean(round_match.group(1))

    parts = [clean(x) for x in detail_line.split(",")]
    if len(parts) >= 2:
        if not round_name:
            round_name = parts[0]
        venue = parts[1]

    crowd_match = re.search(r"Attendance:\s*([\d,]+)", detail_line, re.I)
    if crowd_match:
        crowd = crowd_match.group(1).replace(",", "")

    for fmt in (
        "%A, %d %B %Y, %I:%M %p AEDT",
        "%A, %d %B %Y, %I:%M %p AEST",
        "%A, %dst %B %Y, %I:%M %p AEDT",
        "%A, %dnd %B %Y, %I:%M %p AEDT",
        "%A, %drd %B %Y, %I:%M %p AEDT",
        "%A, %dth %B %Y, %I:%M %p AEDT",
    ):
        try:
            safe_date_line = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_line)
            dt = datetime.strptime(safe_date_line, "%A, %d %B %Y, %I:%M %p AEDT")
            date_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
            break
        except Exception:
            pass
        try:
            safe_date_line = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_line)
            dt = datetime.strptime(safe_date_line, "%A, %d %B %Y, %I:%M %p AEST")
            date_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
            break
        except Exception:
            pass

    return {
        "team_a": team_a,
        "team_b": team_b,
        "outcome": outcome,
        "round": round_name,
        "venue": venue,
        "crowd": crowd,
        "date_iso": date_iso,
        "result_line": result_line,
        "detail_line": detail_line,
        "date_line": date_line,
    }


def extract_scoreboard(soup):
    scoreboard = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        header_cells = [clean(x.get_text(" ")) for x in rows[0].find_all(["th", "td"])]
        if "Final" not in header_cells:
            continue

        for row in rows[1:3]:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            team_name = clean(cells[0].get_text(" "))
            final_score = num(cells[-1].get_text(" "))

            if team_name:
                scoreboard[team_name] = final_score

        if len(scoreboard) >= 2:
            return scoreboard

    return scoreboard


def find_player_tables(soup):
    found = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 8:
            continue

        header_cells = [clean(x.get_text(" ")) for x in rows[0].find_all(["th", "td"])]
        header_set = set(header_cells)

        needed = {"Player", "K", "HB", "D", "M", "G", "B"}
        if not needed.issubset(header_set):
            continue

        title = ""
        prev = table.find_previous(["h1", "h2", "h3", "div", "td"])
        hops = 0
        probe = prev
        while probe and hops < 8:
            txt = clean(probe.get_text(" "))
            if "Player Stats" in txt:
                title = txt
                break
            probe = probe.find_previous(["h1", "h2", "h3", "div", "td"])
            hops += 1

        team_name = ""
        if title:
            m = re.search(r"^(.*?)\s+Player Stats", title, re.I)
            if m:
                team_name = clean(m.group(1))

        found.append({"team": team_name, "table": table})

    return found


def parse_player_table(table):
    rows_out = []

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 18:
            continue

        name = clean(tds[0].get_text(" "))
        if not name:
            continue
        if any(x in name for x in ["AFL", "Attendance", "Round", "Player Stats", "Coach:"]):
            continue
        if len(name.split()) < 2:
            continue

        row = {
            "player": name,
            "K": num(tds[1].get_text(" ")),
            "HB": num(tds[2].get_text(" ")),
            "D": num(tds[3].get_text(" ")),
            "M": num(tds[4].get_text(" ")),
            "G": num(tds[5].get_text(" ")),
            "B": num(tds[6].get_text(" ")),
            "T": num(tds[7].get_text(" ")),
            "HO": num(tds[8].get_text(" ")),
            "GA": num(tds[9].get_text(" ")),
            "I50": num(tds[10].get_text(" ")),
            "CL": num(tds[11].get_text(" ")),
            "CG": num(tds[12].get_text(" ")),
            "R50": num(tds[13].get_text(" ")),
            "FF": num(tds[14].get_text(" ")),
            "FA": num(tds[15].get_text(" ")),
            "AF": num(tds[16].get_text(" ")),
            "SC": num(tds[17].get_text(" ")),
        }
        rows_out.append(row)

    return rows_out


def resolve_table_teams(header_info, player_tables):
    team_a = header_info["team_a"]
    team_b = header_info["team_b"]

    if len(player_tables) < 2:
        return []

    # Best case: both tables have explicit team names
    explicit = [x for x in player_tables if x["team"]]
    if len(explicit) >= 2:
        return player_tables[:2]

    # Fallback: assign by result header order
    player_tables[0]["team"] = team_a
    player_tables[1]["team"] = team_b
    return player_tables[:2]


def parse_match(url, idx):
    print("Scraping:", url)

    soup = BeautifulSoup(get_html(url), "html.parser")
    match_id = f"{YEAR}_{str(idx).zfill(4)}"

    header_info = parse_header_info(soup)
    scoreboard = extract_scoreboard(soup)
    player_tables = find_player_tables(soup)
    player_tables = resolve_table_teams(header_info, player_tables)

    if len(player_tables) < 2:
        print("Skipping match, could not find two player tables")
        return []

    team_names = [clean(x["team"]) for x in player_tables]
    if not team_names[0] or not team_names[1]:
        print("Skipping match, could not resolve team names")
        return []

    rows = []

    for i, item in enumerate(player_tables[:2]):
        team = clean(item["team"])
        opp = clean(player_tables[1 - i]["team"])
        team_score = scoreboard.get(team, 0)
        opp_score = scoreboard.get(opp, 0)

        parsed_rows = parse_player_table(item["table"])

        for r in parsed_rows:
            rows.append({
                "match_id": match_id,
                "season": YEAR,
                "round": header_info["round"],
                "player": r["player"],
                "played_for": team,
                "played_against": opp,
                "K": r["K"],
                "HB": r["HB"],
                "D": r["D"],
                "M": r["M"],
                "G": r["G"],
                "B": r["B"],
                "T": r["T"],
                "HO": r["HO"],
                "GA": r["GA"],
                "I50": r["I50"],
                "CL": r["CL"],
                "CG": r["CG"],
                "R50": r["R50"],
                "FF": r["FF"],
                "FA": r["FA"],
                "AF": r["AF"],
                "SC": r["SC"],
                "date_iso": header_info["date_iso"],
                "venue": header_info["venue"],
                "crowd": header_info["crowd"],
                "team_score": team_score,
                "opp_score": opp_score,
                "team_score_str": format_score(team_score),
                "opp_score_str": format_score(opp_score),
            })

    return rows


def build_players(all_rows):
    players = {}

    stat_keys = ["K", "HB", "D", "M", "G", "B", "T", "HO", "GA", "I50", "CL", "CG", "R50", "FF", "FA", "AF", "SC"]

    for r in all_rows:
        name = r["player"]
        if name not in players:
            players[name] = {
                "player": name,
                "slug": slug(name),
                "games": 0,
                "teams": set(),
            }
            for key in stat_keys:
                players[name][key] = 0

        p = players[name]
        p["games"] += 1
        p["teams"].add(r["played_for"])

        for key in stat_keys:
            p[key] += r.get(key, 0)

    output = []
    for p in players.values():
        team_list = sorted(p["teams"])
        p["teams"] = team_list
        p["team"] = team_list[-1] if team_list else ""
        output.append(p)

    output.sort(key=lambda x: x["player"])
    return output


def main():
    links = get_match_links()
    all_rows = []

    for i, link in enumerate(links, start=1):
        try:
            rows = parse_match(link, i)
            all_rows.extend(rows)
        except Exception as e:
            print("Error parsing match:", link, e)

        time.sleep(1)

    print("TOTAL PLAYER ROWS:", len(all_rows))

    if len(all_rows) < 100:
        print("FAILED - not saving to prevent bad overwrite")
        return

    with open(SEASON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2, ensure_ascii=False)

    players = build_players(all_rows)
    with open(PLAYERS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    print("DONE - season and players updated")


if __name__ == "__main__":
    main()
