import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup


print("BATHURST FULL HISTORY BUILDER")


BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (compatible; BathurstHistoryBuilder/1.0; +https://thesportingalmanac.com)"
    }
)

WIKI_API = "https://en.wikipedia.org/w/api.php"

# Combined history starts in 1960.
# If you want BATHURST VENUE ONLY, change START_YEAR to 1963.
START_YEAR = 1960


def latest_completed_bathurst_year() -> int:
    """
    Bathurst is normally in October.
    Before late October, assume the most recently completed race was the previous year.
    """
    now = datetime.now(timezone.utc)
    if now.month > 10 or (now.month == 10 and now.day >= 20):
        return now.year
    return now.year - 1


END_YEAR = latest_completed_bathurst_year()


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value)
    text = re.sub(r"\[[^\]]+\]", "", text)  # remove citation markers
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if text == "" or text.lower() == "nan":
        return None
    return text


def slugify(text: str) -> str:
    text = clean_text(text) or ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = []
    for col in df.columns:
        if isinstance(col, tuple):
            parts = [clean_text(x) for x in col if clean_text(x)]
            col_name = " ".join(parts)
        else:
            col_name = clean_text(col) or ""
        cols.append(col_name)
    df = df.copy()
    df.columns = cols
    return df


def normalize_column_name(name: str) -> str:
    n = clean_text(name) or ""
    n = n.lower()

    replacements = {
        "pos.": "pos",
        "position": "pos",
        "car no": "no",
        "car number": "no",
        "number": "no",
        "no.": "no",
        "entrant": "team",
        "team/entrant": "team",
        "qual pos": "grid",
        "qualifying pos": "grid",
        "qualifying position": "grid",
        "grid pos": "grid",
        "grid position": "grid",
        "time/retired": "time_or_status",
        "time retired": "time_or_status",
        "time / retired": "time_or_status",
        "retired/time": "time_or_status",
        "race time": "time_or_status",
        "lap time": "time",
        "qualifying": "time",
        "qualifying time": "time",
        "shootout pos": "shootout_position",
        "shootout": "shootout_position",
        "driver(s)": "drivers",
        "driver / co-driver": "drivers",
        "driver": "drivers",
    }

    for old, new in replacements.items():
        if n == old:
            return new

    # partial matches
    if "time/retired" in n or "time retired" in n:
        return "time_or_status"
    if n.startswith("qual") and "grid" not in n and "time" not in n:
        return "grid"
    if n.startswith("grid"):
        return "grid"
    if "shootout" in n and "position" in n:
        return "shootout_position"

    return n


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = flatten_columns(df)
    rename_map = {}
    seen = {}

    for col in df.columns:
        norm = normalize_column_name(col)
        # prevent duplicate column collisions
        if norm in seen:
            seen[norm] += 1
            norm = f"{norm}_{seen[norm]}"
        else:
            seen[norm] = 1
        rename_map[col] = norm

    df = df.rename(columns=rename_map)
    df = df.dropna(how="all")
    df = df.reset_index(drop=True)
    return df


def safe_int(value: Any) -> Optional[int]:
    text = clean_text(value)
    if not text:
        return None
    m = re.search(r"\d+", text)
    if not m:
        return None
    try:
        return int(m.group(0))
    except Exception:
        return None


def page_url_from_title(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"


def wiki_search(query: str) -> List[str]:
    try:
        r = SESSION.get(
            WIKI_API,
            params={
                "action": "opensearch",
                "search": query,
                "limit": 10,
                "namespace": 0,
                "format": "json",
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        return data[1] if len(data) > 1 else []
    except Exception:
        return []


def find_page_title(year: int) -> Optional[str]:
    queries = [
        f"{year} Bathurst 1000",
        f"{year} Bathurst 500",
        f"{year} Armstrong 500",
        f"{year} Gallaher 500",
        f"{year} Hardie-Ferodo 500",
        f"{year} James Hardie 1000",
        f"{year} Tooheys 1000",
        f"{year} AMP Bathurst 1000",
        f"{year} FAI 1000",
        f"{year} Supercheap Auto Bathurst 1000",
        f"{year} Repco Bathurst 1000",
    ]

    keywords = [
        "bathurst",
        "armstrong 500",
        "gallaher 500",
        "hardie-ferodo 500",
        "james hardie 1000",
        "tooheys 1000",
        "amp bathurst 1000",
        "fai 1000",
        "supercheap auto bathurst 1000",
        "repco bathurst 1000",
    ]

    for q in queries:
        results = wiki_search(q)
        for title in results:
            t = title.lower()
            if str(year) in t and any(k in t for k in keywords):
                return title

    # final exact-pattern fallbacks
    fallbacks = [
        f"{year} Bathurst 1000",
        f"{year} Bathurst 500",
        f"{year} Armstrong 500",
        f"{year} Gallaher 500",
        f"{year} Hardie-Ferodo 500",
        f"{year} James Hardie 1000",
        f"{year} Tooheys 1000",
        f"{year} AMP Bathurst 1000",
        f"{year} FAI 1000",
        f"{year} Supercheap Auto Bathurst 1000",
        f"{year} Repco Bathurst 1000",
    ]
    for title in fallbacks:
        test = wiki_search(title)
        if test and test[0].lower() == title.lower():
            return test[0]

    return None


def fetch_page_html(title: str) -> Optional[str]:
    try:
        r = SESSION.get(
            WIKI_API,
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "formatversion": 2,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("parse", {}).get("text")
    except Exception:
        return None


def extract_section_tables(html: str) -> List[Tuple[str, pd.DataFrame]]:
    soup = BeautifulSoup(html, "html.parser")
    section_tables: List[Tuple[str, pd.DataFrame]] = []

    # tables under headings
    for heading in soup.find_all(["h2", "h3"]):
        heading_text = clean_text(heading.get_text(" ", strip=True)) or ""
        node = heading.find_next_sibling()

        while node and node.name not in ["h2", "h3"]:
            if node.name == "table" and "wikitable" in (node.get("class") or []):
                try:
                    dfs = pd.read_html(StringIO(str(node)))
                    for df in dfs:
                        section_tables.append((heading_text, normalize_dataframe(df)))
                except Exception:
                    pass
            node = node.find_next_sibling()

    # fallback: all tables if section headings were not enough
    if not section_tables:
        for table in soup.find_all("table"):
            try:
                dfs = pd.read_html(StringIO(str(table)))
                for df in dfs:
                    section_tables.append(("Unsectioned", normalize_dataframe(df)))
            except Exception:
                pass

    return section_tables


def score_results_table(heading: str, df: pd.DataFrame) -> int:
    cols = set(df.columns)
    score = 0
    h = heading.lower()

    if "result" in h:
        score += 40
    if "official result" in h:
        score += 25

    if "pos" in cols:
        score += 30
    if "drivers" in cols:
        score += 20
    if "car" in cols:
        score += 20
    if "laps" in cols:
        score += 20
    if "team" in cols:
        score += 10
    if "grid" in cols:
        score += 8
    if "time_or_status" in cols:
        score += 8

    score += min(len(df), 100)
    return score


def score_grid_table(heading: str, df: pd.DataFrame) -> int:
    cols = set(df.columns)
    score = 0
    h = heading.lower()

    if "qual" in h:
        score += 40
    if "shootout" in h or "heroes" in h:
        score += 35
    if "grid" in h:
        score += 35

    if "pos" in cols:
        score += 25
    if "drivers" in cols:
        score += 20
    if "car" in cols:
        score += 20
    if "time" in cols:
        score += 20
    if "team" in cols:
        score += 10
    if "no" in cols:
        score += 8

    score += min(len(df), 100)
    return score


def choose_best_tables(section_tables: List[Tuple[str, pd.DataFrame]]) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[pd.DataFrame], Optional[str]]:
    best_results_df = None
    best_results_heading = None
    best_results_score = -1

    best_grid_df = None
    best_grid_heading = None
    best_grid_score = -1

    for heading, df in section_tables:
        r_score = score_results_table(heading, df)
        if r_score > best_results_score:
            best_results_score = r_score
            best_results_df = df
            best_results_heading = heading

        g_score = score_grid_table(heading, df)
        if g_score > best_grid_score:
            best_grid_score = g_score
            best_grid_df = df
            best_grid_heading = heading

    # if chosen "grid" table is clearly not really a grid table, discard it
    if best_grid_df is not None:
        cols = set(best_grid_df.columns)
        if "pos" not in cols or ("drivers" not in cols and "car" not in cols):
            best_grid_df = None
            best_grid_heading = None

    return best_results_df, best_results_heading, best_grid_df, best_grid_heading


def row_to_clean_dict(row: pd.Series) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in row.items():
        k = clean_text(key)
        if not k:
            continue
        out[k] = clean_text(value)
    return out


def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    records = []
    for _, row in df.iterrows():
        clean_row = row_to_clean_dict(row)
        if not any(v for v in clean_row.values()):
            continue
        records.append(clean_row)
    return records


def derive_grid_from_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    starters = []
    seen_numbers = set()

    for row in results:
        grid_val = row.get("grid")
        if not grid_val:
            continue

        number = row.get("no")
        if number and number in seen_numbers:
            continue

        starters.append(
            {
                "grid": grid_val,
                "no": row.get("no"),
                "drivers": row.get("drivers"),
                "team": row.get("team"),
                "car": row.get("car"),
                "source": "results_grid_column",
            }
        )

        if number:
            seen_numbers.add(number)

    starters.sort(key=lambda x: safe_int(x.get("grid")) or 9999)
    return starters


def standardize_grid_records(records: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
    out = []
    for row in records:
        out.append(
            {
                "pos": row.get("pos"),
                "no": row.get("no"),
                "drivers": row.get("drivers"),
                "team": row.get("team"),
                "car": row.get("car"),
                "time": row.get("time") or row.get("qual") or row.get("grid"),
                "grid": row.get("grid"),
                "shootout_position": row.get("shootout_position"),
                "source": source_name,
            }
        )
    return out


def standardize_results_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in records:
        out.append(
            {
                "pos": row.get("pos"),
                "class": row.get("class"),
                "no": row.get("no"),
                "team": row.get("team"),
                "drivers": row.get("drivers"),
                "car": row.get("car"),
                "laps": row.get("laps"),
                "grid": row.get("grid"),
                "shootout_position": row.get("shootout_position"),
                "time_or_status": row.get("time_or_status"),
            }
        )
    return out


def detect_venue(year: int) -> str:
    return "Phillip Island" if year <= 1962 else "Mount Panorama, Bathurst"


def build_year(year: int) -> Optional[Dict[str, Any]]:
    print(f"\n--- {year} ---")

    page_title = find_page_title(year)
    if not page_title:
        print(f"No page found for {year}")
        return None

    print(f"Page: {page_title}")

    html = fetch_page_html(page_title)
    if not html:
        print(f"Could not fetch page HTML for {year}")
        return None

    section_tables = extract_section_tables(html)
    if not section_tables:
        print(f"No tables found for {year}")
        return None

    results_df, results_heading, grid_df, grid_heading = choose_best_tables(section_tables)

    results_records = []
    grid_records = []
    grid_source = None

    if results_df is not None:
        results_records = standardize_results_records(dataframe_to_records(results_df))

    if grid_df is not None:
        grid_records = standardize_grid_records(
            dataframe_to_records(grid_df),
            "qualifying_table",
        )
        grid_source = grid_heading

    if not grid_records and results_records:
        derived = derive_grid_from_results(results_records)
        if derived:
            grid_records = derived
            grid_source = "derived_from_results_grid_column"

    data = {
        "year": year,
        "event_page_title": page_title,
        "source_url": page_url_from_title(page_title),
        "venue": detect_venue(year),
        "metadata": {
            "results_section": results_heading,
            "grid_section": grid_heading,
            "grid_source": grid_source,
            "results_found": bool(results_records),
            "grid_found": bool(grid_records),
            "notes": (
                "Wikipedia page structures vary by year. Early years may only have class-style results "
                "and may not contain a full structured starting grid."
            ),
        },
        "starting_grid": grid_records,
        "results": results_records,
    }

    out_file = SEASONS_DIR / f"{year}.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Saved {out_file} | grid={len(grid_records)} | results={len(results_records)}"
    )
    return data


def build_index(year_summaries: List[Dict[str, Any]]) -> None:
    index = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "years": year_summaries,
    }
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {INDEX_FILE}")


def main() -> None:
    year_summaries = []

    for year in range(START_YEAR, END_YEAR + 1):
        try:
            data = build_year(year)
            if not data:
                year_summaries.append(
                    {
                        "year": year,
                        "file": f"seasons/{year}.json",
                        "venue": detect_venue(year),
                        "found": False,
                        "results_found": False,
                        "grid_found": False,
                    }
                )
                continue

            year_summaries.append(
                {
                    "year": year,
                    "file": f"seasons/{year}.json",
                    "venue": data.get("venue"),
                    "found": True,
                    "results_found": data["metadata"].get("results_found", False),
                    "grid_found": data["metadata"].get("grid_found", False),
                    "page_title": data.get("event_page_title"),
                    "source_url": data.get("source_url"),
                    "results_count": len(data.get("results", [])),
                    "grid_count": len(data.get("starting_grid", [])),
                }
            )
        except Exception as e:
            print(f"FAILED {year}: {e}")
            year_summaries.append(
                {
                    "year": year,
                    "file": f"seasons/{year}.json",
                    "venue": detect_venue(year),
                    "found": False,
                    "results_found": False,
                    "grid_found": False,
                    "error": str(e),
                }
            )

    build_index(year_summaries)
    print("\nDONE")


if __name__ == "__main__":
    main()bathu
