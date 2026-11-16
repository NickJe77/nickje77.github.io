// Shared helpers: column mapping, CSV, horse names, dates.

// [CSV heading, database column]. Headings are matched ignoring case, spaces and punctuation.
export const COLUMNS: [string, string][] = [
  ["Track", "track"], ["Date", "date"], ["Race", "race"], ["Race Name", "race_name"],
  ["Position", "position"], ["Starters", "starters"], ["Finish Time", "finish_time"],
  ["Weight", "weight"], ["Distance", "distance"], ["Horse", "horse"], ["Margin", "margin"],
  ["Starting Odds", "starting_odds"], ["Prize Money", "prize_money"],
  ["Position 400", "pos_400"], ["Position 800", "pos_800"], ["Position 1200", "pos_1200"],
  ["Rating", "rating"], ["Race Grade", "race_grade"], ["TAB Meeting", "tab_meeting"],
  ["Metro", "metro"], ["Track Condition", "track_condition"],
  ["Track Condition Numeric", "track_condition_numeric"], ["State", "state"],
  ["Jockey", "jockey"], ["Trainer", "trainer"], ["Horse Age", "horse_age"],
  ["Barrier", "barrier"], ["Class", "class"], ["Race Type", "race_type"],
];
export const DB_COLS = COLUMNS.map((c) => c[1]);

export const headingKey = (s: string) => (s || "").toLowerCase().replace(/[^a-z0-9]/g, "");

export function normHorse(name: string): string {
  let s = (name || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  s = s.replace(/\s*\([a-z]{2,4}\)\s*$/, "");
  return s.replace(/[^a-z0-9]/g, "");
}

/** Excel turns race times like 1-40 into dates ("Jan-40", "40-Jan", "1/01/1940"): put them back to 1-40.00 */
const MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
export function fixTime(t: string): string {
  t = (t || "").trim();
  let m = t.match(/^([A-Za-z]{3})[-\s]?(\d{1,2}(?:\.\d+)?)$/) || null, mins = -1, secs = "";
  if (m && MONTHS.includes(m[1].toLowerCase())) { mins = MONTHS.indexOf(m[1].toLowerCase()) + 1; secs = m[2]; }
  else if ((m = t.match(/^(\d{1,2})[-\s]([A-Za-z]{3})$/)) && MONTHS.includes(m[2].toLowerCase())) { mins = MONTHS.indexOf(m[2].toLowerCase()) + 1; secs = m[1]; }
  if (mins < 0) return t;
  const [w, f = ""] = secs.split(".");
  return `${mins}-${w.padStart(2, "0")}.${(f + "00").slice(0, 2)}`;
}

export function raceNo(r: string): string {
  const m = (r || "").match(/\d+/);
  return m ? String(parseInt(m[0], 10)) : (r || "").trim();
}

/** 15/11/26, 15/11/2026, 2026-11-15 -> 2026-11-15 */
export function isoDate(d: string): string | null {
  d = (d || "").trim();
  let m = d.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (m) return `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}`;
  m = d.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2}|\d{4})$/);
  if (!m) return null;
  let y = m[3];
  if (y.length === 2) y = (parseInt(y, 10) > 50 ? "19" : "20") + y;
  const day = parseInt(m[1], 10), mon = parseInt(m[2], 10);
  if (mon < 1 || mon > 12 || day < 1 || day > 31) return null;
  return `${y}-${String(mon).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/** 2026-11-15 -> 15/11/2026 (the form guide's style) */
export function auDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${parseInt(d, 10)}/${parseInt(m, 10)}/${y}`;
}

export function shiftDay(iso: string, days: number): string {
  const t = Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) + days * 86400000;
  return new Date(t).toISOString().slice(0, 10);
}

/** '3YO, Class 2, Handicap, Class 2, Handicap' -> '3YO, Class 2, Handicap' */
export function tidyClass(c: string | null | undefined): string {
  const seen = new Set<string>(), out: string[] = [];
  for (const p of (c || "").split(",")) {
    const t = p.trim();
    if (t && !seen.has(t.toLowerCase())) { seen.add(t.toLowerCase()); out.push(t); }
  }
  return out.join(", ");
}

// ---------------------------------------------------------------- CSV
export function parseCSV(text: string): string[][] {
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
  const rows: string[][] = [];
  let row: string[] = [], field = "", i = 0, q = false;
  const n = text.length;
  while (i < n) {
    const c = text[i];
    if (q) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 2; continue; }
        q = false; i++; continue;
      }
      field += c; i++; continue;
    }
    if (c === '"') { q = true; i++; continue; }
    if (c === ",") { row.push(field); field = ""; i++; continue; }
    if (c === "\r") { i++; continue; }
    if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; i++; continue; }
    field += c; i++;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  return rows.filter((r) => r.some((c) => c.trim() !== ""));
}

export function csvCell(v: unknown): string {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
export const csvLine = (cells: unknown[]) => cells.map(csvCell).join(",") + "\r\n";

// ---------------------------------------------------------------- rows from an uploaded CSV
export interface Row {
  [col: string]: string;
}

/** Map CSV rows onto database columns. Unknown headings go into `extra` (JSON). */
export function rowsFromCSV(table: string[][]): { rows: Row[]; unknown: string[]; bad: number } {
  const hdr = table[0].map((h) => h.trim());
  const byKey = new Map(COLUMNS.map(([h, c]) => [headingKey(h), c]));
  const map = hdr.map((h) => byKey.get(headingKey(h)) || null);
  const unknown = hdr.filter((h, i) => h && !map[i]);
  const rows: Row[] = [];
  let bad = 0;
  for (const r of table.slice(1)) {
    const o: Row = {};
    const extra: Record<string, string> = {};
    r.forEach((v, i) => {
      v = (v || "").trim();
      if (map[i]) o[map[i]!] = v;
      else if (hdr[i] && v) extra[hdr[i]] = v;
    });
    const iso = isoDate(o.date || "");
    if (!iso || !o.track || !o.horse) { bad++; continue; }
    o.date = iso;
    o.track = o.track.toUpperCase();
    o.race = raceNo(o.race || "");
    if (o.finish_time) o.finish_time = fixTime(o.finish_time);
    o.horse_key = normHorse(o.horse);
    if (Object.keys(extra).length) o.extra = JSON.stringify(extra);
    rows.push(o);
  }
  return { rows, unknown, bad };
}
