import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE = "https://www.daviscup.com"
YEAR = "2025"

SECTION_PATHS = [
    f"/en/draws-results/{YEAR}/qualifiers",
    f"/en/draws-results/{YEAR}/world-group-i",
    f"/en/draws-results/{YEAR}/world-group-ii",
    f"/en/draws-results/{YEAR}/finals",
]

OUTPUT = Path(f"docs/data/tennis/davis_cup/{YEAR}.json")
DEBUG_DIR = Path(f"docs/data/tennis/davis_cup/debug/{YEAR}")

SCORE_RE = re.compile(
    r"(?:(?:\d{1,2}[-–]\d{1,2})(?:\(\d+\))?\s*){2,5}|W/O|RET|DEF|ABN",
    re.IGNORECASE,
)

SECTION_SLUGS = {"qualifiers", "world-group-i", "world-group-ii", "finals"}


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def slug_path(url: str) -> str:
    return urlparse(url).path.rstrip("/")


def is_candidate_tie_url(url: str) -> bool:
    path = slug_path(url)
    if not path.startswith(f"/en/draws-results/{YEAR}/"):
        return False

    parts = [p for p in path.split("/") if p]
    # /en/draws-results/2025/qualifiers -> 4 parts after filtering
    # /en/draws-results/2025/qualifiers/spain-vs-switzerland -> 5 parts
    if len(parts) < 5:
        return False

    last = parts[-1].lower()
    if last in SECTION_SLUGS:
        return False

    if any(x in last for x in ["draws-results", "tickets", "news", "teams", "players"]):
        return False

    return True


def safe_goto(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightTimeoutError:
        pass


def collect_links(page, url: str) -> list[str]:
    safe_goto(page, url)

    hrefs = page.eval_on_selector_all(
        "a[href]",
        """
        els => els.map(a => a.href).filter(Boolean)
        """,
    )

    out = []
    seen = set()
    for href in hrefs:
        full = urljoin(BASE, href)
        if is_candidate_tie_url(full) and full not in seen:
            seen.add(full)
            out.append(full)
    return out


def extract_title(page) -> str:
    candidates = [
        "h1",
        "main h1",
        "[class*='title']",
        "[class*='heading']",
    ]
    for sel in candidates:
        try:
            txt = clean(page.locator(sel).first.inner_text(timeout=1500))
            if txt:
                return txt
        except Exception:
            pass
    return clean(page.title())


def extract_match_rows_from_dom(page) -> list[dict]:
    js = """
    () => {
      const nodes = Array.from(document.querySelectorAll("tr, li, article, section, div"));
      const rows = [];
      for (const n of nodes) {
        const txt = (n.innerText || "").replace(/\\s+/g, " ").trim();
        if (!txt) continue;
        if (txt.length < 12 || txt.length > 300) continue;
        rows.push(txt);
      }
      return Array.from(new Set(rows));
    }
    """
    texts = page.evaluate(js)

    rows = []
    seen = set()

    for txt in texts:
        text = clean(txt)
        if not text:
            continue

        lower = text.lower()
        if "singles" not in lower and "doubles" not in lower and "match " not in lower:
            continue
        if not SCORE_RE.search(text):
            continue

        match_type = "Doubles" if "doubles" in lower else "Singles"

        key = (match_type, text)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "match_type": match_type,
                "raw_text": text,
            }
        )

    return rows


def enrich_rows(rows: list[dict]) -> list[dict]:
    enriched = []

    for row in rows:
        raw = row["raw_text"]
        score_match = SCORE_RE.search(raw)
        score = score_match.group(0).strip() if score_match else ""

        pre_score = raw
        if score:
            pre_score = raw[: score_match.start()].strip()

        # remove obvious labels
        pre_score = re.sub(r"(?i)^match\\s*\\d+\\s*", "", pre_score).strip()
        pre_score = re.sub(r"(?i)\\b(singles|doubles)\\b", "", pre_score).strip(" -–:|")

        enriched.append(
            {
                "match_type": row["match_type"],
                "score": score,
                "raw_text": raw,
                "players_text": clean(pre_score),
            }
        )

    return enriched


def scrape_tie(page, url: str) -> dict:
    safe_goto(page, url)

    title = extract_title(page)
    rows = enrich_rows(extract_match_rows_from_dom(page))

    return {
        "tie_url": url,
        "tie_title": title,
        "matches": rows,
    }


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    all_tie_links = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for section_path in SECTION_PATHS:
            section_url = urljoin(BASE, section_path)
            print(f"SECTION: {section_url}")
            links = collect_links(page, section_url)
            print(f"  ties found: {len(links)}")

            for link in links:
                if link not in seen:
                    seen.add(link)
                    all_tie_links.append(link)

        print(f"TOTAL UNIQUE TIES: {len(all_tie_links)}")

        dataset = []

        for i, tie_url in enumerate(all_tie_links, start=1):
            print(f"[{i}/{len(all_tie_links)}] {tie_url}")
            try:
                tie_data = scrape_tie(page, tie_url)

                # keep only ties where we actually found match rows
                if tie_data["matches"]:
                    dataset.append(tie_data)

                    debug_name = tie_url.rstrip("/").split("/")[-1] + ".json"
                    with open(DEBUG_DIR / debug_name, "w", encoding="utf-8") as f:
                        json.dump(tie_data, f, indent=2, ensure_ascii=False)
                else:
                    print("  no match rows found")
            except Exception as e:
                print(f"  ERROR: {e}")

        browser.close()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    tie_count = len(dataset)
    match_count = sum(len(t["matches"]) for t in dataset)
    doubles_count = sum(
        1 for t in dataset for m in t["matches"] if m.get("match_type") == "Doubles"
    )

    print(f"✅ saved ties: {tie_count}")
    print(f"✅ saved matches: {match_count}")
    print(f"✅ saved doubles: {doubles_count}")
    print(f"✅ output: {OUTPUT}")


if __name__ == "__main__":
    main()
