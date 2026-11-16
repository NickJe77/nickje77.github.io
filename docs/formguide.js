/* The Sporting Almanac — Form Guide
   Loads results from the form guide database on Cloudflare and fills each page.
   Pages: form-guide.html, meeting.html, race.html, horse.html, comparison.html, blackbook.html */
(function () {
  "use strict";
  const API = window.FG_API || "https://formguide.thesportingalmanac.workers.dev";
  const SPELL_DAYS = 84;                        // 12 weeks between runs = a spell (first-up next time)

  // ------------------------------------------------------------ small helpers
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const qs = (k) => new URLSearchParams(location.search).get(k) || "";
  const DAY = 86400000;
  const toDate = (iso) => new Date(iso + "T12:00:00");
  const days = (a, b) => Math.round((toDate(b) - toDate(a)) / DAY);
  const todayISO = () => new Date(Date.now() + 10 * 3600000).toISOString().slice(0, 10);
  const fmtDate = (iso, long) => !iso ? "" : toDate(iso).toLocaleDateString("en-AU",
    long ? { weekday: "long", day: "numeric", month: "long", year: "numeric" } : { day: "2-digit", month: "short", year: "2-digit" });
  const num = (v) => { const n = parseFloat(String(v ?? "").replace(/[^0-9.\-]/g, "")); return isNaN(n) ? null : n; };
  const money = (v) => { const n = num(v); return n ? "$" + Math.round(n).toLocaleString("en-AU") : "—"; };
  const dash = (v) => (v === null || v === undefined || v === "" ? "—" : v);

  // some names arrive with HTML codes in them ("&amp;", "&#8217;"): turn them back into characters
  const unent = (v) => typeof v !== "string" || v.indexOf("&") < 0 ? v : v.replace(/&#(\d+);/g, (m, n) => String.fromCharCode(Number(n)))
    .replace(/&#x([0-9a-f]+);/gi, (m, n) => String.fromCharCode(parseInt(n, 16))).replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  // one spelling per jockey: "Fred W Kersley" / "Fred W. Kersley" -> "Fred Kersley" (middle initials dropped), "FRED KERSLEY" -> "Fred Kersley"
  function personName(v) {
    let w = String(v || "").replace(/\s+/g, " ").trim().split(" ");
    if (w.length >= 3) w = [w[0], ...w.slice(1, -1).filter((x) => !/^[A-Za-z]\.?$/.test(x)), w[w.length - 1]];
    const t = w.join(" ");
    return /[a-z]/.test(t) ? t : t.toLowerCase().replace(/(^|[\s'-])([a-z])/g, (m, p, c) => p + c.toUpperCase());
  }
  async function get(path) {
    const r = await fetch(API + path);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || "HTTP " + r.status);
    return JSON.parse(await r.text(), (k, v) => k === "jockey" && typeof v === "string" ? personName(unent(v)) : unent(v));
  }

  // ------------------------------------------------------------ tracks, horses, races
  const TRACKS = window.TRACKS || {};
  const AU = new Set(["NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT"]);
  const TYPE_ORDER = ["Metro", "Provincial", "Country", "Picnic", "International", ""];
  // track names -> codes, so venue names from the fields feed ("Pakenham") find your entry (PAKM)
  const nameKey = (n) => String(n || "").toLowerCase().replace(/\(.*?\)/g, "").replace(/[^a-z0-9]/g, "");
  const BY_NAME = {};
  Object.entries(TRACKS).forEach(([c, t]) => { const k = nameKey(t[0]); if (k) (BY_NAME[k] ||= []).push(c); });
  // same name in two countries (Ascot WA / Ascot UK): pick the one in the right country
  const byName = (n, intl) => { const l = BY_NAME[nameKey(n)] || []; return l.find((c) => AU.has(TRACKS[c][1]) !== intl) || (l.length === 1 && TRACKS[l[0]][2] !== "International" && !intl ? l[0] : null); };
  // overseas track codes seen in the CSV form (Nmkt, Asc., Newb…): name and country
  const ABBR = {
    asc: ["Ascot", "GB"], ascot: ["Ascot", "GB"], ayr: ["Ayr", "GB"], bath: ["Bath", "GB"], bevl: ["Beverley", "GB"], bev: ["Beverley", "GB"],
    brig: ["Brighton", "GB"], brgh: ["Brighton", "GB"], carl: ["Carlisle", "GB"], catt: ["Catterick", "GB"], chel: ["Cheltenham", "GB"],
    ches: ["Chester", "GB"], chst: ["Chester", "GB"], chep: ["Chepstow", "GB"], donc: ["Doncaster", "GB"], epsm: ["Epsom", "GB"], epsom: ["Epsom",
    "GB"], ffos: ["Ffos Las", "GB"], good: ["Goodwood", "GB"], gdwd: ["Goodwood", "GB"], hami: ["Hamilton", "GB"], hmtn: ["Hamilton", "GB"],
    hayd: ["Haydock", "GB"], kemp: ["Kempton", "GB"], kmpt: ["Kempton", "GB"], leic: ["Leicester", "GB"], ling: ["Lingfield", "GB"],
    muss: ["Musselburgh", "GB"], newb: ["Newbury", "GB"], newc: ["Newcastle", "GB"], ncsl: ["Newcastle", "GB"], nmkt: ["Newmarket", "GB"],
    newm: ["Newmarket", "GB"], nmkj: ["Newmarket (July)", "GB"], nott: ["Nottingham", "GB"], pont: ["Pontefract", "GB"], redc: ["Redcar", "GB"],
    ripn: ["Ripon", "GB"], ripo: ["Ripon", "GB"], sals: ["Salisbury", "GB"], sand: ["Sandown Park", "GB"], sthw: ["Southwell", "GB"],
    souw: ["Southwell", "GB"], thir: ["Thirsk", "GB"], wind: ["Windsor", "GB"], winds: ["Windsor", "GB"], wolv: ["Wolverhampton", "GB"],
    wolvs: ["Wolverhampton", "GB"], warw: ["Warwick", "GB"], wrwk: ["Warwick", "GB"], yarm: ["Yarmouth", "GB"], york: ["York", "GB"],
    curr: ["The Curragh", "IRE"], curragh: ["The Curragh", "IRE"], leop: ["Leopardstown", "IRE"], fair: ["Fairyhouse", "IRE"], gowr: ["Gowran Park",
    "IRE"], dund: ["Dundalk", "IRE"], galw: ["Galway", "IRE"], naas: ["Naas", "IRE"], navn: ["Navan", "IRE"], nava: ["Navan", "IRE"],
    punc: ["Punchestown", "IRE"], tipp: ["Tipperary", "IRE"], list: ["Listowel", "IRE"], lstl: ["Listowel", "IRE"], cork: ["Cork", "IRE"],
    kill: ["Killarney", "IRE"], limk: ["Limerick", "IRE"], rosc: ["Roscommon", "IRE"], slig: ["Sligo", "IRE"], tram: ["Tramore", "IRE"],
    wexf: ["Wexford", "IRE"], bell: ["Bellewstown", "IRE"], ball: ["Ballinrobe", "IRE"], down: ["Down Royal", "GB"], lchp: ["Longchamp", "FR"],
    long: ["Longchamp", "FR"], chan: ["Chantilly", "FR"], deau: ["Deauville", "FR"], stcl: ["Saint-Cloud", "FR"], mlaf: ["Maisons-Laffitte",
    "FR"], shat: ["Sha Tin", "HK"], shtn: ["Sha Tin", "HK"], hapv: ["Happy Valley", "HK"], toky: ["Tokyo", "JPN"], kyot: ["Kyoto", "JPN"],
    hans: ["Hanshin", "JPN"], naka: ["Nakayama", "JPN"], meyd: ["Meydan", "UAE"], belm: ["Belmont Park", "USA"], sara: ["Saratoga", "USA"],
    keen: ["Keeneland", "USA"], chur: ["Churchill Downs", "USA"] };
  // names to show differently from how the feed spells them
  const RENAME = { parislongchamp: "Longchamp" };
  const shortCode = (c) => /^[A-Z0-9 .]{2,5}$/.test(c || "");
  function track(code, extra) {
    const x = extra || {};
    // overseas? from the venue's country, else a non-Australian state/country on the row (GBR, FRA, USA…)
    const st = String(x.venue_country || x.state || x.venue_state || "").toUpperCase();
    const intl = st ? !(AU.has(st) || /^AU/.test(st)) : /-(fr|gbr|ire|usa|jpn|ger|ity|can|brz|saf|uae|hk)$/i.test(code || "");
    const c = TRACKS[code] ? code : TRACKS[(code || "").toUpperCase()] ? (code || "").toUpperCase()
      : byName(x.venue_name, intl) || byName(String(code || "").replace(/-(fr|gbr|ire|usa|jpn|ger|ity|nz|aus|can|brz|saf)$/i, "").replace(/-/g, " "), intl);
    const t = c && TRACKS[c];
    if (t) return { code, show: shortCode(c) ? c : "", name: t[0], state: t[1], type: t[2], aus: AU.has(t[1]) };
    const ab = !x.venue_name && ABBR[String(code || "").toLowerCase().replace(/[^a-z]/g, "")];
    if (ab && !(st && AU.has(st))) return { code, show: shortCode(code) ? code : "", name: ab[0], state: ab[1], type: "International", aus: false };
    const name = x.venue_name || String(code || "").replace(/-(fr|gbr|ire|usa|jpn|ger|ity|nz|aus)$/i, "").replace(/-/g, " ").toLowerCase().replace(/\b\w/g, (m) => m.toUpperCase());
    return { code, show: shortCode(code) ? code : "", name: RENAME[nameKey(name)] || name, state: intl ? (x.venue_country || st) : (x.venue_state || (AU.has(st) ? st : "")), type: intl ? "International" : "Country", aus: !intl };
  }
  const fmtTime = (iso) => !iso ? "" : new Date(iso).toLocaleTimeString("en-AU", { timeZone: "Australia/Melbourne", hour: "numeric", minute: "2-digit" });
  const isScr = (r) => Number(r.scratched) === 1;
  const wt = (r) => r.weight ? r.weight + (r.claim && r.claim !== "0" ? ` <span class="mini">(a${esc(r.claim)})</span>` : "") : "—";
  const horseKey = (n) => String(n || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().trim()
    .replace(/\s*\([a-z]{2,4}\)\s*$/, "").replace(/[^a-z0-9]/g, "");
  const pos = (r) => { const n = parseInt(r.position, 10); return isNaN(n) ? null : n; };
  const posLabel = (r) => { const p = pos(r); if (!p) return dash(r.position); const s = ["th", "st", "nd", "rd"], v = p % 100; return p + (s[(v - 20) % 10] || s[v] || s[0]); };
  const going = (r) => { const t = String(r.track_condition || "").toLowerCase();
    return t.startsWith("good") ? "Good" : t.startsWith("soft") ? "Soft" : t.startsWith("heavy") ? "Heavy" : t.startsWith("synth") ? "Synthetic" : t.startsWith("firm") ? "Firm" : (r.track_condition || ""); };
  const goingLabel = (r) => [going(r), r.track_condition_numeric && r.track_condition_numeric !== "0" ? r.track_condition_numeric : ""].filter(Boolean).join(" ");
  const grade = (r) => r.race_grade || "";
  function classLabel(r) {
    if (r.race_grade) return r.race_grade;
    const c = String(r.class || "").split(",").map((x) => x.trim()).filter(Boolean);
    const main = c.find((x) => /^(BM|Class|Group|Listed|Maiden|Rating|Restricted|CL|F&M|Open|Hcp|Handicap)/i.test(x) && !/^Handicap$/i.test(x)) || c[0] || "";
    return main.replace(/^Group (\d)$/i, "G$1").replace(/^Listed$/i, "LR");
  }
  const dist = (r) => num(r.distance);
  const WORDS = { TRPHY: "Trophy", TRPY: "Trophy", TPHY: "Trophy", MDN: "Maiden", NOV: "Novice", NOVS: "Novice", HCP: "Handicap", HCAP: "Handicap", "H'CAP": "Handicap",
    STKS: "Stakes", STK: "Stakes", CLM: "Claiming", CLMG: "Claiming", ALW: "Allowance", ALWC: "Allowance", FIL: "Fillies", FILS: "Fillies", MRS: "Mares", CND: "Conditions",
    COND: "Conditions", INTL: "International", MEM: "Memorial", CHAMP: "Championship", CHMP: "Championship", APP: "Apprentice", APPR: "Apprentice", AMAT: "Amateur", SPR: "Sprint" };
  const KEEP = /^(G[123]|LR|SW|SWP|WFA|BM\d*|F&M|CL\d*|MSW|TAB|ATC|VRC|MRC|QTC|AJC|SAJC|WATC|BRC|RL|PB|NZ|UK|USA|[IVX]{2,5}|[0-9]+YO\+?|[0-9]+[A-Z]?)$/;
  const SMALL = new Set(["of", "the", "and", "at", "in", "for", "on", "by", "to", "a", "de", "du", "la", "le"]);
  function raceName(v) {
    const t = String(v || "").trim();
    if (!t || /[a-z]/.test(t)) return t;                  // already in normal case
    return t.split(/(\s+|-|\/)/).map((w, i) => {
      if (/^(\s+|-|\/)$/.test(w) || !w) return w;
      if (WORDS[w]) return WORDS[w];
      const m = w.match(/^(\d+)Y(O?)(\+?)$/); if (m) return m[1] + "yo" + m[3];
      if (KEEP.test(w)) return w;
      const low = w.toLowerCase();
      if (i > 0 && SMALL.has(low)) return low;
      if (i > 0 && /^[ld]'[a-z]/.test(low)) return low.slice(0, 2) + low.charAt(2).toUpperCase() + low.slice(3);   // de l'Arc, d'Or
      return low.replace(/^([^a-z]*)([a-z])/, (x, p, c) => p + c.toUpperCase()).replace(/'([a-z])([a-z]+)/, (x, a, b) => "'" + a.toUpperCase() + b);
    }).join("");
  }
  // race time for display: 1-40.00 -> 1:40.00, and Excel's "Jan-40" -> 1:40.00
  const MON = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
  function runTime(v) {
    let t = String(v || "").trim(), m;
    if ((m = t.match(/^([A-Za-z]{3})[-:\s]?(\d{1,2})(\.\d+)?$/)) && MON.includes(m[1].toLowerCase())) t = `${MON.indexOf(m[1].toLowerCase()) + 1}:${m[2].padStart(2, "0")}${m[3] || ".00"}`;
    else if ((m = t.match(/^(\d{1,2})[-\s]([A-Za-z]{3})$/)) && MON.includes(m[2].toLowerCase())) t = `${MON.indexOf(m[2].toLowerCase()) + 1}:${m[1].padStart(2, "0")}.00`;
    return dash(t.replace("-", ":"));
  }
  const timeSecs = (v) => { const t = runTime(v); if (t === "—") return null; const p = t.split(":"); const x = p.length > 1 ? Number(p[0]) * 60 + Number(p[1]) : Number(p[0]); return x > 0 ? x : null; };
  const SECS_PER_LENGTH = 0.17;
  // class band, same rules as Cloudflare: each stakes level on its own, the rest by benchmark
  function classBand(r) {
    const g = String(r.race_grade || "").toUpperCase(), c = String(r.class || "").toUpperCase();
    if (["G1", "G2", "G3", "LR"].includes(g)) return g;
    if (c.includes("GROUP 1")) return "G1"; if (c.includes("GROUP 2")) return "G2"; if (c.includes("GROUP 3")) return "G3"; if (c.includes("LISTED")) return "LR";
    const bm = c.match(/(?:BENCHMARK|BM)\s*(\d+)/);
    if (/BM|BENCHMARK/.test(c)) { const n = bm ? Number(bm[1]) : 0; return n >= 78 ? "High" : n >= 64 ? "Mid" : n > 0 ? "Low" : "Other"; }
    if (/OPEN|QUALITY|CLASS [456]/.test(c)) return "High";
    if (/CLASS [23]/.test(c)) return "Mid";
    if ((c.includes("MAIDEN") && !c.includes("MAIDENS INELIGIBLE")) || /CLASS 1|RESTRICTED|RATING/.test(c)) return "Low";
    return "Other";
  }
  const BAND_NAME = { G1: "Group 1", G2: "Group 2", G3: "Group 3", LR: "Listed", High: "BM78+ / Open", Mid: "BM64–77", Low: "BM63 & below / Maiden" };
  const avgKey = (r, b) => `${String(r.track || "").toUpperCase()}|${parseInt(r.distance, 10) || 0}|${going(r)}|${b}`;
  // "+2.4L" (faster than the average winner) / "−1.1L" (slower), shaded green/red by how far.
  // Compared with winners of the same class band; falls back to all classes when there are fewer than 3.
  function vsAverage(r, avgs) {
    const band = classBand(r), t = timeSecs(r.finish_time);
    let a = band !== "Other" && avgs && avgs[avgKey(r, band)], same = true;
    if (!a || a.n < 3) { a = avgs && avgs[avgKey(r, "*")]; same = false; }
    if (!a || a.n < 3 || t === null) return `<td class="mini" title="${a ? "Only " + a.n + " race" + (a.n === 1 ? "" : "s") + " to average" : "No average yet"}">—</td>`;
    const L = Math.round((a.avg - t) / SECS_PER_LENGTH * 10) / 10, k = Math.min(1, Math.abs(L) / 8);
    const bg = L > 0 ? `rgba(22,163,74,${(0.08 + 0.32 * k).toFixed(2)})` : L < 0 ? `rgba(220,38,38,${(0.08 + 0.32 * k).toFixed(2)})` : "transparent";
    const avgTxt = Math.floor(a.avg / 60) + ":" + (a.avg % 60).toFixed(2).padStart(5, "0");
    const what = same ? BAND_NAME[band] + " races" : "races of all classes" + (band !== "Other" ? " (not enough " + BAND_NAME[band] + " races yet)" : "");
    return `<td style="background:${bg};font-weight:600" title="Average winning time: ${avgTxt} — ${a.n} ${esc(what)} at ${esc(track(r.track).name)} ${parseInt(r.distance, 10)}m, ${esc(going(r) || "any going")}">${L > 0 ? "+" : L < 0 ? "−" : ""}${Math.abs(L).toFixed(1)}L${same ? "" : '<span class="mini">*</span>'}</td>`;
  }
  const raceURL = (r) => `race.html?track=${encodeURIComponent(r.track)}&date=${r.date}&race=${r.race}`;
  const meetingURL = (t, d) => `meeting.html?track=${encodeURIComponent(t)}&date=${d}`;
  // ---- same name, different horses (Lady Catalina in Australia and another in the USA)
  // Runs are grouped by the country they were run in (Australia + NZ count as one, so do Britain + Ireland),
  // and two countries are joined when the same trainer had the horse in both (an Irish raider in the Melbourne Cup).
  const CC = { NZL: "NZ", UK: "GBR", GB: "GBR", ENG: "GBR", IRL: "IRE", RSA: "SAF", ZAF: "SAF", US: "USA", HKG: "HK", JAP: "JPN" };
  const countryOf = (r) => { const t = track(r.track, r); if (t.aus) return "AUS"; const c = String(t.state || "").toUpperCase().replace(/[^A-Z]/g, ""); return CC[c] || c || "INT"; };
  const regionOf = (r) => { const c = countryOf(r); return c === "AUS" || c === "NZ" ? "ANZ" : c === "GBR" || c === "IRE" ? "GBI" : c; };
  const trainerKeys = (t) => String(t || "").toLowerCase().split(/\s*(?:&|\/|,|\band\b)\s*/).map((x) => {
    const w = x.replace(/[^a-z\s]/g, " ").trim().split(/\s+/).filter(Boolean); return w.length ? (w.length > 1 ? w[0][0] : "") + w[w.length - 1] : ""; }).filter((k) => k.length > 2);
  // Groups of runs that are one horse. Within a country, different trainers at the same time = different horses;
  // a trainer change from one period to the next = the same horse changing stables.
  function horseGroups(runs) {
    const units = {};                                   // region|trainer -> runs
    runs.forEach((r) => { const k = regionOf(r) + "|" + (trainerKeys(r.trainer)[0] || "?"); (units[k] ||= []).push(r); });
    const keys = Object.keys(units), parent = Object.fromEntries(keys.map((k) => [k, k]));
    const find = (k) => parent[k] === k ? k : (parent[k] = find(parent[k]));
    const join = (a, b) => { a = find(a); b = find(b); if (a !== b) parent[b] = a; };
    // the same trainer (or partner) anywhere = the same horse (an Irish raider in Melbourne)
    const byTrainer = {};
    keys.forEach((k) => units[k].forEach((r) => trainerKeys(r.trainer).forEach((t) => (byTrainer[t] ||= new Set()).add(k))));
    Object.values(byTrainer).forEach((set) => { const l = [...set]; l.slice(1).forEach((k) => join(l[0], k)); });
    // within a region: join stables one after the other; keep apart stables racing at the same time
    const span = (k) => { const ds = keys.filter((x) => find(x) === k).flatMap((x) => units[x].map((r) => r.date)).sort(); return [ds[0], ds[ds.length - 1]]; };
    const byRegion = {};
    keys.forEach((k) => (byRegion[k.split("|")[0]] ||= new Set()).add(find(k)));
    Object.values(byRegion).forEach((set) => {
      const roots = [...set].filter((k) => !k.endsWith("|?"));
      let changed = true;
      while (changed) {
        changed = false;
        const live = [...new Set(roots.map(find))].map((k) => ({ k, s: span(k) })).sort((a, b) => a.s[0].localeCompare(b.s[0]));
        for (let i = 0; i < live.length && !changed; i++) for (let j = i + 1; j < live.length && !changed; j++) {
          const A = live[i], B = live[j], gap = days(A.s[1], B.s[0]);
          // one ends (give or take two weeks) before the other starts: same horse, new stable
          if (gap >= -14 && !live.some((C, n) => n !== i && n !== j && C.s[0] < B.s[0] && C.s[1] > A.s[1])) { join(A.k, B.k); changed = true; }
        }
      }
      // runs with no trainer go with the biggest group in that region
      [...set].filter((k) => k.endsWith("|?")).forEach((k) => {
        const others = [...new Set(roots.map(find))];
        if (others.length) join(others.sort((a, b) => keys.filter((x) => find(x) === b).reduce((n, x) => n + units[x].length, 0) - keys.filter((x) => find(x) === a).reduce((n, x) => n + units[x].length, 0))[0], k);
      });
    });
    const groups = {};
    keys.forEach((k) => { const g = (groups[find(k)] ||= { regions: new Set(), runs: [] }); g.runs.push(...units[k]); g.regions.add(k.split("|")[0]); });
    const out = Object.values(groups).map((g) => {
      const n = {}; g.runs.forEach((r) => { const c = countryOf(r); n[c] = (n[c] || 0) + 1; });
      g.runs.sort((a, b) => b.date.localeCompare(a.date));
      return { ...g, country: Object.entries(n).sort((a, b) => b[1] - a[1])[0][0], latest: g.runs[0] };
    }).sort((a, b) => (b.regions.has("ANZ") - a.regions.has("ANZ")) || b.latest.date.localeCompare(a.latest.date));
    // horses that move country (an Irish import to Ciaron Maher, an Australian horse sold to Hong Kong):
    // one career ends before the other starts, within two years, and the ages agree -> the same horse
    const span2 = (g) => [g.runs[g.runs.length - 1].date, g.runs[0].date];
    const foaled = (g) => { const y = g.runs.map((r) => parseInt(r.date, 10) - parseInt(r.horse_age, 10)).filter((x) => x > 1990); return y.length ? y.sort()[Math.floor(y.length / 2)] : null; };
    // where the horse was bred, from the name: "Beautiful You (NZ)" -> NZ (most common across the group's runs)
    const BRED = { GB: "GBR", UK: "GBR", IRE: "IRE", IRL: "IRE", NZ: "NZ", NZL: "NZ", USA: "USA", US: "USA", FR: "FR", FRA: "FR", JPN: "JPN", GER: "GER", AUS: "AUS", ARG: "ARG", BRZ: "BRZ", SAF: "SAF", CHI: "CHI", ITY: "ITY", HK: "HK" };
    const bredIn = (g) => { const n = {}; g.runs.forEach((r) => { const m = String(r.horse || "").match(/\(([A-Za-z]{2,4})\)\s*$/); if (m) { const c = BRED[m[1].toUpperCase()] || m[1].toUpperCase(); n[c] = (n[c] || 0) + 1; } });
      const e = Object.entries(n).sort((x, y) => y[1] - x[1])[0]; return e ? e[0] : null; };
    const homeOf = (g) => { const n = {}; g.runs.forEach((r) => { const c = countryOf(r); n[c] = (n[c] || 0) + 1; }); return Object.entries(n).sort((x, y) => y[1] - x[1])[0][0]; };
    const fits = (A, B) => {
      if ([...A.regions].some((x) => B.regions.has(x))) return false;
      // the bred-in country has to agree: (IRE) in Ireland and (IRE) in Australia is one horse;
      // a (NZ) horse here and a horse with no suffix racing in the USA are two (it would be "(NZ)" over there too)
      const ba = bredIn(A), bb = bredIn(B);
      if (ba && bb && ba !== bb) return false;
      if (ba && !bb && homeOf(B) !== ba) return false;
      if (bb && !ba && homeOf(A) !== bb) return false;
      const [a0, a1] = span2(A), [b0, b1] = span2(B), first = a0 <= b0 ? [a1, b0] : [b1, a0], gap = days(first[0], first[1]);
      const fa = foaled(A), fb = foaled(B);
      return gap >= -14 && gap <= 730 && !(fa && fb && Math.abs(fa - fb) > 1);
    };
    for (let again = true; again && out.length > 1;) {
      again = false;
      for (const A of out) {
        const cand = out.filter((B) => B !== A && fits(A, B));
        // only when it's clear-cut: A fits exactly one group, and that group fits only A
        if (cand.length === 1 && out.filter((C) => C !== cand[0] && fits(cand[0], C)).length === 1) {
          const B = cand[0], [keep, drop] = A.regions.has("ANZ") || A.runs.length >= B.runs.length ? [A, B] : [B, A];
          keep.runs = [...keep.runs, ...drop.runs].sort((x, y) => y.date.localeCompare(x.date)); drop.regions.forEach((x) => keep.regions.add(x));
          keep.latest = keep.runs[0]; out.splice(out.indexOf(drop), 1); again = true; break;
        }
      }
    }
    out.forEach((g) => { const n = {}; g.runs.forEach((r) => { const c = countryOf(r); n[c] = (n[c] || 0) + 1; }); g.country = g.regions.has("ANZ") ? "AUS" : Object.entries(n).sort((x, y) => y[1] - x[1])[0][0]; });
    const seen = {};
    out.forEach((g) => { seen[g.country] = (seen[g.country] || 0) + 1; g.id = g.country + (seen[g.country] > 1 ? "-" + seen[g.country] : ""); });
    return out;
  }
  // the runs that belong to the same horse as "ref" (a run or a field entry)
  function sameHorse(runs, ref) {
    if (!runs || !runs.length || !ref) return runs || [];
    const gs = horseGroups(runs); if (gs.length < 2) return runs;
    const tk = new Set(trainerKeys(ref.trainer)), rg = regionOf(ref);
    const g = gs.find((x) => x.runs.some((r) => trainerKeys(r.trainer).some((k) => tk.has(k))))
      || gs.filter((x) => x.regions.has(rg)).sort((a, b) => Math.abs(days(a.latest.date, ref.date || todayISO())) - Math.abs(days(b.latest.date, ref.date || todayISO())))[0];
    return g ? g.runs : [];
  }
  const fixHistory = (card) => { (card.runs || []).forEach((r) => { if (card.history && card.history[r.horse_key]) card.history[r.horse_key] = sameHorse(card.history[r.horse_key], r); }); return card; };
  const horseURL = (n, r) => `horse.html?horse=${encodeURIComponent(n)}` + (r && r.track ? "&c=" + countryOf(r) : "")
    + (r && trainerKeys(r.trainer)[0] ? "&t=" + encodeURIComponent(trainerKeys(r.trainer)[0]) : "");
  const silk = (r, big) => r && r.silk ? `<img class="silk${big ? " big" : ""}" src="${esc(r.silk)}" alt="" loading="lazy">` : `<span class="silk none${big ? " big" : ""}"></span>`;
  const horseCell = (r) => `<span class="horsecell">${silk(r)}<a href="${horseURL(r.horse, r)}">${esc(r.horse)}</a></span>`;

  // records like "24: 5-3-4"
  function record(runs) {
    let w = 0, s = 0, t = 0, n = 0;
    for (const r of runs) { const p = pos(r); if (p === null && !r.position) continue; n++; if (p === 1) w++; else if (p === 2) s++; else if (p === 3) t++; }
    return { n, w, s, t, text: n ? `${n}: ${w}-${s}-${t}` : "—", win: n ? (100 * w / n) : 0, place: n ? (100 * (w + s + t) / n) : 0 };
  }
  // last-N figure, newest last: "x21x3", 0 = 10th or worse, x = spell
  function figure(desc, n = 10) {
    const runs = desc.slice(0, n).reverse();
    let out = "";
    runs.forEach((r, i) => {
      if (i > 0 && days(runs[i - 1].date, r.date) >= SPELL_DAYS) out += "x";
      const p = pos(r); out += p === null ? "-" : p >= 10 ? "0" : String(p);
    });
    return out || "—";
  }
  // tag each run (oldest first) as first-up / second-up
  function upTags(desc) {
    const asc = [...desc].reverse(), tag = new Map();
    asc.forEach((r, i) => {
      if (i === 0 || days(asc[i - 1].date, r.date) >= SPELL_DAYS) tag.set(r, 1);
      else if (tag.get(asc[i - 1]) === 1) tag.set(r, 2);
    });
    return tag;
  }
  const near = (a, b, tol = 50) => a !== null && b !== null && Math.abs(a - b) <= tol;

  // a horse's stats from earlier runs (newest first), relative to a run "at"
  function horseStats(prior, at) {
    const tags = upTags(prior.concat(at ? [] : []));
    const last = prior[0];
    const d = at ? dist(at) : null;
    return {
      career: record(prior),
      last10: figure(prior, 10), last5: figure(prior, 5),
      dist: at ? record(prior.filter((r) => near(dist(r), d))) : null,
      going: at ? record(prior.filter((r) => going(r) === going(at))) : null,
      track: at ? record(prior.filter((r) => r.track === at.track)) : null,
      trackDist: at ? record(prior.filter((r) => r.track === at.track && near(dist(r), d))) : null,
      jockey: at ? record(prior.filter((r) => r.jockey && r.jockey === at.jockey)) : null,
      firstUp: record(prior.filter((r) => tags.get(r) === 1)),
      secondUp: record(prior.filter((r) => tags.get(r) === 2)),
      daysSince: at && last ? days(last.date, at.date) : null,
      last,
    };
  }

  // ------------------------------------------------------------ accounts (email + password, kept on Cloudflare)
  const TOKEN = "tsa-token", EMAIL = "tsa-email";
  const store = { get: (k) => { try { return localStorage.getItem(k) || ""; } catch (e) { return ""; } },
                  set: (k, v) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch (e) { /* storage blocked */ } } };
  const loggedIn = () => !!store.get(TOKEN);
  async function api(path, method = "GET", body) {
    const r = await fetch(API + path, { method, headers: { authorization: "Bearer " + store.get(TOKEN), ...(body ? { "content-type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined });
    const d = await r.json().catch(() => ({}));
    if (r.status === 401 && path.indexOf("/api/auth/login") < 0 && path.indexOf("/api/auth/signup") < 0) { store.set(TOKEN, ""); store.set(EMAIL, ""); }
    if (!r.ok) throw new Error(d.error || "Something went wrong (" + r.status + ")");
    return d;
  }

  // ------------------------------------------------------------ blackbook (this browser's copy; saved to your account when logged in)
  const BOOK = "tsa-blackbook";
  function book() { try { return JSON.parse(localStorage.getItem(BOOK) || "{}"); } catch (e) { return {}; } }
  function saveBook(b) {
    const old = book();
    try { localStorage.setItem(BOOK, JSON.stringify(b)); } catch (e) { /* storage blocked */ }
    if (!loggedIn()) return;
    // send only what changed to the account
    Object.keys(b).forEach((h) => { if (!old[h] || old[h].note !== b[h].note) api("/api/blackbook", "PUT", { horse: h, note: b[h].note || "", added: b[h].added || "" }).catch(() => {}); });
    Object.keys(old).forEach((h) => { if (!b[h]) api("/api/blackbook?horse=" + encodeURIComponent(h), "DELETE").catch(() => {}); });
  }
  // when logged in, the account's blackbook is the one shown
  async function syncBook() {
    if (!loggedIn()) return;
    try { const b = await api("/api/blackbook"); try { localStorage.setItem(BOOK, JSON.stringify(b)); } catch (e) { /* storage blocked */ } } catch (e) { /* offline: keep this browser's copy */ }
  }
  function toggleBook(name) { const b = book(); if (b[name]) delete b[name]; else b[name] = { note: "", added: todayISO() }; saveBook(b); return !!b[name]; }

  function accountUI() {
    const nav = $("header nav"); if (!nav) return;
    let el = $("#acct"); if (!el) { el = document.createElement("span"); el.id = "acct"; nav.after(el); }
    if (loggedIn()) {
      el.innerHTML = `<button class="acctbtn" id="acctmenu">${esc(store.get(EMAIL))} ▾</button><div class="acctdrop hidden" id="acctdrop">
        <a href="blackbook.html">My Blackbook</a><button data-pw>Change password</button><button data-out>Log out</button></div>`;
      $("#acctmenu").onclick = (e) => { e.stopPropagation(); $("#acctdrop").classList.toggle("hidden"); };
      document.addEventListener("click", () => $("#acctdrop") && $("#acctdrop").classList.add("hidden"));
      $("[data-out]", el).onclick = async () => { await api("/api/auth/logout", "POST").catch(() => {}); store.set(TOKEN, ""); store.set(EMAIL, ""); store.set(BOOK, ""); location.reload(); };
      $("[data-pw]", el).onclick = () => signIn("password");
    } else {
      el.innerHTML = `<button class="acctbtn primary" id="acctlogin">Log in</button>`;
      $("#acctlogin").onclick = () => signIn("login");
    }
  }
  const resetToken = qs("reset");
  function signIn(mode) {
    const box = document.createElement("div");
    box.className = "modalback";
    const draw = () => {
      const pw = mode === "password", forgot = mode === "forgot", reset = mode === "reset";
      if (forgot || reset) {
        box.innerHTML = `<div class="modal" role="dialog" aria-modal="true"><button class="x" title="Close">×</button>
          <h2>${forgot ? "Forgot your password?" : "Choose a new password"}</h2>
          <p class="note">${forgot ? "Enter your email and we'll send you a link to choose a new one." : "Pick a new password for your account (8+ characters)."}</p>
          <form>${forgot ? `<label>Email<input class="field" type="email" name="email" autocomplete="email" required></label>`
            : `<label>New password<input class="field" type="password" name="password" autocomplete="new-password" minlength="8" required></label>`}
            <p class="err hidden"></p><p class="ok hidden"></p><button class="primary" type="submit">${forgot ? "Email me a link" : "Save new password"}</button></form>
          <p class="note swap"><a href="#" data-m="login">Back to log in</a></p></div>`;
        $(".x", box).onclick = () => box.remove();
        $$("[data-m]", box).forEach((a) => a.onclick = (e) => { e.preventDefault(); mode = a.dataset.m; draw(); });
        $("form", box).onsubmit = async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(e.target)), err = $(".err", box), ok = $(".ok", box), btn = $("button[type=submit]", box);
          btn.disabled = true; err.classList.add("hidden");
          try {
            if (forgot) { const r = await api("/api/auth/forgot", "POST", f); ok.textContent = r.message; ok.classList.remove("hidden"); $("label", box).classList.add("hidden"); btn.classList.add("hidden"); return; }
            const r = await api("/api/auth/reset", "POST", { token: resetToken, password: f.password });
            store.set(TOKEN, r.token); store.set(EMAIL, r.email);
            const local = book(); if (Object.keys(local).length) await api("/api/blackbook", "POST", { book: local }).catch(() => {});
            await syncBook();
            history.replaceState(null, "", location.pathname); location.reload();
          } catch (x) { err.textContent = x.message; err.classList.remove("hidden"); btn.disabled = false; }
        };
        const f0 = $("input", box); if (f0) f0.focus();
        return;
      }
      box.innerHTML = `<div class="modal" role="dialog" aria-modal="true"><button class="x" title="Close">×</button>
        <h2>${pw ? "Change password" : mode === "login" ? "Log in" : "Create an account"}</h2>
        <p class="note">${pw ? "Other devices will be logged out." : "Save your blackbook to your account and see it on any device."}</p>
        <form>${pw ? `<label>Current password<input class="field" type="password" name="old" autocomplete="current-password" required></label>
          <label>New password<input class="field" type="password" name="new" autocomplete="new-password" minlength="8" required></label>`
          : `<label>Email<input class="field" type="email" name="email" autocomplete="email" required></label>
          <label>Password${mode === "signup" ? " <span class='mini'>(8+ characters)</span>" : ""}<input class="field" type="password" name="password" autocomplete="${mode === "signup" ? "new-password" : "current-password"}" minlength="${mode === "signup" ? 8 : 1}" required></label>`}
          <p class="err hidden"></p><button class="primary" type="submit">${pw ? "Change password" : mode === "login" ? "Log in" : "Create account"}</button></form>
        ${pw ? "" : `<p class="note swap">${mode === "login" ? "<a href='#' data-m='forgot'>Forgot password?</a> · New here? <a href='#' data-m='signup'>Create an account</a>" : "Already have one? <a href='#' data-m='login'>Log in</a>"}</p>`}</div>`;
      $(".x", box).onclick = () => box.remove();
      $$("[data-m]", box).forEach((a) => a.onclick = (e) => { e.preventDefault(); mode = a.dataset.m; draw(); });
      $("form", box).onsubmit = async (e) => {
        e.preventDefault();
        const f = Object.fromEntries(new FormData(e.target)), err = $(".err", box), btn = $("button[type=submit]", box);
        btn.disabled = true; err.classList.add("hidden");
        try {
          const r = await api(pw ? "/api/auth/password" : "/api/auth/" + mode, "POST", f);
          store.set(TOKEN, r.token); store.set(EMAIL, r.email);
          if (!pw) {
            // bring the horses saved in this browser into the account
            const local = book(); if (Object.keys(local).length) await api("/api/blackbook", "POST", { book: local }).catch(() => {});
            await syncBook();
          }
          location.reload();
        } catch (x) { err.textContent = x.message; err.classList.remove("hidden"); btn.disabled = false; }
      };
      const first = $("input", box); if (first) first.focus();
    };
    draw();
    box.onclick = (e) => { if (e.target === box) box.remove(); };
    document.body.appendChild(box);
  }

  // ------------------------------------------------------------ shared UI
  function tabs(container) {
    const root = typeof container === "string" ? $(container) : container;
    if (!root) return;
    $$("button", root).forEach((b) => b.onclick = () => {
      $$("button", root).forEach((x) => x.classList.toggle("active", x === b));
      $$("[data-tabcontent]").forEach((p) => p.classList.toggle("hidden", p.dataset.tabcontent !== b.dataset.panel));
    });
  }
  const loading = (el) => { if (el) el.innerHTML = `<div class="loading">Loading…</div>`; };
  const fail = (el, e) => { if (el) el.innerHTML = `<div class="error">Couldn't load the data (${esc(e.message || e)}). Try refreshing.</div>`; };
  const groupBy = (arr, f) => arr.reduce((m, x) => { const k = f(x); (m[k] ||= []).push(x); return m; }, {});

  // ------------------------------------------------------------ interactive speed map
  // Starting positions: actual settling position (results) or predicted from the last 5 runs (upcoming).
  // You can drag horses between columns / reorder them, and choose the pace. Saved per race in this browser.
  const COLS = ["Leaders", "On pace", "Midfield", "Back"];
  const PACES = ["Slow", "Moderate", "Genuine", "Fast"];
  // how each pace treats each column: + helps, - hurts
  const PACE_FX = { Slow: [2, 1, -1, -2], Moderate: [1, 1, 0, -1], Genuine: [0, 1, 1, 0], Fast: [-2, -1, 1, 2] };
  const MAPKEY = "tsa-speedmaps";
  const loadMaps = () => { try { return JSON.parse(localStorage.getItem(MAPKEY) || "{}"); } catch (e) { return {}; } };
  const saveMaps = (m) => { try { localStorage.setItem(MAPKEY, JSON.stringify(m)); } catch (e) { /* storage blocked */ } };

  function initialPlacement(runs, history, upcoming) {
    const live = runs.filter((r) => !isScr(r));
    let est;
    if (upcoming) {
      est = live.map((r) => {
        const prior = ((history || {})[r.horse_key] || []).slice(0, 5)
          .map((h) => { const p = num(h.pos_800) ?? num(h.pos_400), n = num(h.starters); return p && n ? (p - 1) / Math.max(1, n - 1) : null; })
          .filter((x) => x !== null);
        return { r, v: prior.length ? prior.reduce((a, b) => a + b, 0) / prior.length : null };
      });
    } else {
      const n = live.length;
      est = live.map((r) => { const p = num(r.pos_800) ?? num(r.pos_400); return { r, v: p ? (p - 1) / Math.max(1, n - 1) : null }; });
    }
    const col = (v) => v === null ? 2 : v < .2 ? 0 : v < .45 ? 1 : v < .75 ? 2 : 3;   // no data: midfield
    const out = {};
    est.sort((a, b) => (a.v ?? .6) - (b.v ?? .6)).forEach((e, i) => out[e.r.horse_key] = { c: col(e.v), o: i, guess: e.v === null });
    return out;
  }
  function suggestPace(place) {
    const leaders = Object.values(place).filter((p) => p.c === 0).length, pace = Object.values(place).filter((p) => p.c <= 1).length;
    return leaders >= 4 || pace >= 7 ? "Fast" : leaders === 3 ? "Genuine" : leaders <= 1 ? "Slow" : "Moderate";
  }


  // ------------------------------------------------------------ virtual race
  // Each horse gets a rating in lengths from its recent runs (class of race + how far it was beaten), adjusted for
  // today's distance/going/track record, weight, first-up, barrier, where you've put it on the speed map, the pace
  // you've chosen and any track bias. The race is then run 1,000 times with some luck added to each horse.
  const CLASS_PTS = { G1: 12, G2: 10, G3: 8, LR: 6, High: 4, Mid: 2, Low: 0, Other: 1 };
  const BIAS_STRENGTH = { slight: 1, moderate: 2, strong: 3.5 };
  const PATTERN_FX = { none: [0, 0, 0, 0], leaders: [1, 0.5, -0.25, -0.6], back: [-0.6, -0.25, 0.4, 1] };
  const LANE_FX = { none: [0, 0, 0, 0], rail: [1, 0.5, 0, -0.5], railoff: [-1, -0.6, -0.1, 0.4], wide: [-0.6, -0.2, 0.3, 0.8] };   // by column: leaders hug the rail, backmarkers come wide
  function gauss() { let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  const placeRate = (list) => list.length ? list.filter((r) => { const p = pos(r); return p && p <= 3; }).length / list.length : null;

  function horseModel(r, prior, today, field) {
    const notes = [];
    const recent = (prior || []).slice(0, 8);
    let sum = 0, wsum = 0;
    recent.forEach((h, i) => {
      const p = pos(h); if (!p) return;
      let beaten = num(h.margin);
      if (p === 1) beaten = -1;                                   // a win counts a length better than a narrow second
      else if (beaten === null) beaten = (p - 1) * 1.2;
      const perf = CLASS_PTS[classBand(h)] - Math.min(beaten, 15), w = Math.pow(0.82, i);
      sum += perf * w; wsum += w;
    });
    const nEff = wsum, raw = wsum ? sum / wsum : null;
    let adj = 0;
    const add = (v, why) => { if (Math.abs(v) >= 0.3) notes.push((v > 0 ? "+" : "−") + Math.abs(v).toFixed(1) + "L " + why); adj += v; };
    if (recent.length) {
      const career = placeRate(prior);
      const suit = (list, why) => { if (list.length >= 2 && career !== null) add(Math.max(-1.5, Math.min(1.5, 3 * (placeRate(list) - career))), why); };
      suit(prior.filter((h) => near(dist(h), today.dist, 150)), "at the distance");
      suit(prior.filter((h) => going(h) && going(h) === today.going), "on the going");
      suit(prior.filter((h) => h.track === today.track), "at the track");
      const last = prior[0], gap = last ? days(last.date, today.date) : 0;
      if (gap >= SPELL_DAYS) {
        const tags = upTags(prior), fu = prior.filter((h) => tags.get(h) === 1);
        if (fu.length >= 2 && career !== null) add(Math.max(-2, Math.min(1.5, 3 * (placeRate(fu) - career))), "first-up record");
        else add(-0.8, "first-up");
      }
      const best = Math.max(...prior.filter((h) => pos(h) && pos(h) <= 3).map(dist).filter(Boolean), 0);
      if (today.dist && best && today.dist > best + 400) add(-1, "untried this far");
    } else notes.push("no race form");
    const w = num(r.weight) - (num(r.claim) || 0);
    if (w && field.avgWeight) add(-(w - field.avgWeight) * (0.4 + (today.dist || 1400) / 6000), "weight");
    return { raw, nEff, adj, notes, unknown: !recent.length };
  }

  function runVirtualRace(live, place, pace, history, today, bias) {
    const ws = live.map((r) => num(r.weight) - (num(r.claim) || 0)).filter((x) => x);
    const field = { avgWeight: ws.length ? ws.reduce((a, b) => a + b, 0) / ws.length : null };
    const models = live.map((r) => ({ r, ...horseModel(r, (history || {})[r.horse_key] || [], today, field) }));
    const known = models.filter((m) => m.raw !== null), mean = known.length ? known.reduce((a, m) => a + m.raw, 0) / known.length : 0;
    const S = BIAS_STRENGTH[bias.strength] || 3, fx = PACE_FX[pace];
    models.forEach((m) => {
      // little form -> pulled towards the field average; no form -> a bit below it
      m.base = m.raw === null ? mean - 2.5 : (m.nEff * m.raw + 1.5 * mean) / (m.nEff + 1.5);
      const p = place[m.r.horse_key] || { c: 2, o: 0 }, c = p.c;
      const add = (v, why) => { if (Math.abs(v) >= 0.3) m.notes.push((v > 0 ? "+" : "−") + Math.abs(v).toFixed(1) + "L " + why); m.adj += v; };
      add(fx[c] * 1.5, COLS[c].toLowerCase() + " in a " + pace.toLowerCase() + " pace");
      const b = num(m.r.barrier);
      if (b && b > 8 && c >= 1 && (today.dist || 0) < 1600) add(-0.15 * (b - 8), "wide barrier");
      if (b && b > 8 && c === 0) add(-0.1 * (b - 8), "crossing from wide");
      add(PATTERN_FX[bias.pattern][c] * S, "track pattern");
      add(LANE_FX[bias.lane][c] * S, "lane bias");
      m.score = m.base + m.adj;
      m.sd = m.unknown ? 3.2 : 2 + 3 / (1 + m.nEff);
      m.wins = 0; m.top3 = 0; m.posSum = 0;
    });
    const N = 1000;
    for (let i = 0; i < N; i++) {
      const out = models.map((m) => ({ m, v: m.score + gauss() * m.sd })).sort((a, b) => b.v - a.v);
      out.forEach((o, j) => { if (j === 0) o.m.wins++; if (j < 3) o.m.top3++; o.m.posSum += j + 1; });
    }
    models.forEach((m) => { m.winPct = 100 * m.wins / N; m.top3Pct = 100 * m.top3 / N; m.avgPos = m.posSum / N; });
    const order = [...models].sort((a, b) => b.score - a.score);
    order.forEach((m) => { m.margin = Math.max(0, order[0].score - m.score); });
    return order;
  }

  function speedMapEditor(el, runs, history, upcoming, key) {
    const live = runs.filter((r) => !isScr(r));
    const byKey = Object.fromEntries(live.map((r) => [r.horse_key, r]));
    const start = initialPlacement(runs, history, upcoming), suggested = suggestPace(start);
    const maps = loadMaps(), saved = maps[key];
    let place = saved && saved.place && Object.keys(saved.place).length ? { ...start, ...saved.place } : JSON.parse(JSON.stringify(start));
    Object.keys(place).forEach((k) => { if (!byKey[k]) delete place[k]; });
    let pace = (saved && saved.pace) || suggested;
    let bias = (saved && saved.bias) || { pattern: "none", lane: "none", strength: "moderate" }, simShown = false;
    const edited = () => !!(saved && (saved.edited || saved.pace));
    el.innerHTML = `<div data-map></div><div data-sim class="simwrap"></div>`;
    const mapEl = $("[data-map]", el), simEl = $("[data-sim]", el);
    const r0 = live[0] || runs[0] || {};
    const today = { dist: dist(r0), going: going(r0), track: r0.track, date: r0.date || todayISO() };

    function persist(isEdit) {
      const m = loadMaps();
      m[key] = { place, pace, bias, edited: isEdit || (m[key] && m[key].edited) || false, at: Date.now() };
      const keys = Object.keys(m); if (keys.length > 300) keys.sort((a, b) => m[a].at - m[b].at).slice(0, keys.length - 300).forEach((k) => delete m[k]);
      saveMaps(m);
    }
    function move(k, c, beforeKey) {
      const list = (col) => Object.keys(place).filter((x) => place[x].c === col && x !== k).sort((a, b) => place[a].o - place[b].o);
      const target = list(c), i = beforeKey ? target.indexOf(beforeKey) : -1;
      target.splice(i < 0 ? target.length : i, 0, k);
      place[k].c = c;
      COLS.forEach((_, ci) => (ci === c ? target : list(ci)).forEach((x, j) => place[x].o = ci * 100 + j));
      persist(true); draw(); if (simShown) simulate(false);
    }
    function nudge(k, dc, dy) {
      const p = place[k];
      if (dc) return move(k, Math.max(0, Math.min(3, p.c + dc)));
      const col = Object.keys(place).filter((x) => place[x].c === p.c).sort((a, b) => place[a].o - place[b].o), i = col.indexOf(k), j = i + dy;
      if (j < 0 || j >= col.length) return;
      move(k, p.c, dy < 0 ? col[j] : col[j + 1]);
    }
    function draw() {
      const fx = PACE_FX[pace];
      const tone = (v) => v > 0 ? `<span class="fx good">${v > 1 ? "Big advantage" : "Advantage"}</span>` : v < 0 ? `<span class="fx bad">${v < -1 ? "Big disadvantage" : "Disadvantage"}</span>` : `<span class="fx">Neutral</span>`;
      mapEl.innerHTML = `<div class="maptools">
          <span class="mini">Pace:</span>${PACES.map((x) => `<button class="filter ${x === pace ? "active" : ""}" data-pace="${x}">${x}${x === suggested ? " •" : ""}</button>`).join("")}
          <span class="mini">• suggested from the likely leaders</span><span style="flex:1"></span><button data-reset>Reset</button></div>
        <div class="speedmap">${COLS.map((c, ci) => `<div class="mapcol ${fx[ci] > 0 ? "good" : fx[ci] < 0 ? "bad" : ""}" data-col="${ci}"><h4>${c} ${tone(fx[ci])}</h4>${Object.keys(place)
          .filter((k) => place[k].c === ci).sort((a, b) => place[a].o - place[b].o).map((k) => { const r = byKey[k];
            const fin = !upcoming && pos(r) ? ` → ${posLabel(r)}` : "";
            return `<div class="runner" draggable="true" data-k="${esc(k)}" title="Drag to move">${silk(r)}<span class="rname">${r.number ? esc(r.number) + ". " : ""}${esc(r.horse)} <span class="mini">(b${dash(r.barrier)}${fin})${place[k].guess ? " ?" : ""}</span></span>
              <span class="nudge"><button data-n="${esc(k)}" data-dc="-1" title="Further forward">◀</button><button data-n="${esc(k)}" data-dy="-1" title="Up">▲</button><button data-n="${esc(k)}" data-dy="1" title="Down">▼</button><button data-n="${esc(k)}" data-dc="1" title="Further back">▶</button></span></div>`; }).join("") || '<span class="mini droph">Drop horses here</span>'}</div>`).join("")}</div>
        <p class="pad note" style="padding-top:0">${upcoming ? "Starting positions are predicted from where each horse settled in its last 5 runs (? = no settling data yet)." : "Starting positions are where each horse settled at the 800m (or 400m), with where it finished."}
          Drag horses to change the map, or use the arrows. Your map and pace are saved in this browser.</p>`;
      $$("[data-pace]", mapEl).forEach((b) => b.onclick = () => { pace = b.dataset.pace; persist(false); draw(); });
      if (simShown) simulate(false);                       // keep the virtual race in step with the map
      $("[data-reset]", mapEl).onclick = () => { const m = loadMaps(); delete m[key]; saveMaps(m); place = JSON.parse(JSON.stringify(start)); pace = suggested; bias = { pattern: "none", lane: "none", strength: "moderate" }; draw(); simControls(); simShown = false; };
      $$("[data-n]", mapEl).forEach((b) => b.onclick = (e) => { e.stopPropagation(); nudge(b.dataset.n, Number(b.dataset.dc || 0), Number(b.dataset.dy || 0)); });
      // drag and drop
      $$(".runner[data-k]", mapEl).forEach((d) => {
        d.ondragstart = (e) => { e.dataTransfer.setData("text/plain", d.dataset.k); e.dataTransfer.effectAllowed = "move"; d.classList.add("dragging"); };
        d.ondragend = () => d.classList.remove("dragging");
      });
      $$(".mapcol", mapEl).forEach((col) => {
        col.ondragover = (e) => { e.preventDefault(); col.classList.add("over"); };
        col.ondragleave = () => col.classList.remove("over");
        col.ondrop = (e) => {
          e.preventDefault(); col.classList.remove("over");
          const k = e.dataTransfer.getData("text/plain"); if (!place[k]) return;
          const below = $$(".runner[data-k]", col).filter((x) => x.dataset.k !== k).find((x) => e.clientY < x.getBoundingClientRect().top + x.offsetHeight / 2);
          move(k, Number(col.dataset.col), below ? below.dataset.k : null);
        };
      });
    }

    // ---- the virtual race panel
    function simControls() {
      const opt = (name, cur, list) => `<select class="field" data-b="${name}">${list.map(([v, t]) => `<option value="${v}" ${v === cur ? "selected" : ""}>${t}</option>`).join("")}</select>`;
      simEl.innerHTML = `<div class="simtools">
          <button class="primary" data-run>▶ Run virtual race</button>
          <label>Track pattern ${opt("pattern", bias.pattern, [["none", "No bias"], ["leaders", "Leaders favoured"], ["back", "Swoopers favoured"]])}</label>
          <label>Lane ${opt("lane", bias.lane, [["none", "No bias"], ["rail", "Rail fast"], ["railoff", "Rail off (inside slow)"], ["wide", "Out wide favoured"]])}</label>
          <label>Strength ${opt("strength", bias.strength, [["slight", "Slight"], ["moderate", "Moderate"], ["strong", "Strong"]])}</label>
        </div><div data-simout></div>`;
      $("[data-run]", simEl).onclick = () => simulate(true);
      $$("[data-b]", simEl).forEach((s) => s.onchange = () => { bias[s.dataset.b] = s.value; persist(false); if (simShown) simulate(false); });
    }
    function simulate(animate) {
      simShown = true;
      const order = runVirtualRace(live, place, pace, history, today, bias), out = $("[data-simout]", simEl);
      const actual = !upcoming && live.some((r) => pos(r));
      out.innerHTML = `<div class="simtrack" data-anim></div>
        <div class="tablewrap"><table><thead><tr><th>Projected</th><th class="name">Horse</th><th>Margin</th><th>Win %</th><th>Top 3 %</th><th>Avg finish</th>${actual ? "<th>Actual</th>" : ""}<th class="name">Why</th></tr></thead><tbody>
        ${order.map((m, i) => `<tr class="${i === 0 ? "win" : ""}"><td><b>${posLabel({ position: String(i + 1) })}</b></td><td class="name"><span class="horsecell">${silk(m.r)}${m.r.number ? esc(m.r.number) + ". " : ""}${esc(m.r.horse)}</span></td>
          <td>${i ? m.margin.toFixed(1) + "L" : "—"}</td><td><b>${m.winPct.toFixed(0)}%</b></td><td>${m.top3Pct.toFixed(0)}%</td><td>${m.avgPos.toFixed(1)}</td>${actual ? `<td>${posLabel(m.r)}</td>` : ""}
          <td class="name mini">${esc(m.notes.join(" · ") || "—")}</td></tr>`).join("")}</tbody></table></div>
        <p class="pad note" style="padding-top:6px">A guide, not a tip: 1,000 runs of the race from each horse's recent form (class and margins), its record at the distance, going and track,
          weight, first-up record and barrier, with your speed map, pace${bias.pattern !== "none" || bias.lane !== "none" ? " and track bias" : ""}. Win % is how often it won those 1,000 runs.
          <button data-replay class="filter">↻ Replay</button></p>`;
      $("[data-replay]", out).onclick = () => animateRace($("[data-anim]", out), order);
      animateRace($("[data-anim]", out), order, !animate);
    }
    // the race on screen: they jump in speed-map order, the field closes up, then it finishes the way the model projects
    function animateRace(box, order, still) {
      const byNo = [...order].sort((a, b) => (num(a.r.number) || 99) - (num(b.r.number) || 99) || a.r.horse.localeCompare(b.r.horse));
      const early = (m) => { const p = place[m.r.horse_key] || { c: 2, o: 200 }; return [0, 2.5, 5.5, 9][p.c] + (p.o % 100) * 0.8; };
      const fin = (m) => Math.min(m.margin, 18);
      box.innerHTML = `<div class="simfinish"></div><div class="simlabels"><span>Start</span><span>800m</span><span>400m</span><span>Finish</span></div>` + byNo.map((m) =>
        `<div class="simlane"><span class="simhorse" data-h="${esc(m.r.horse_key)}">${silk(m.r)}${m.r.number ? `<span class="simno">${esc(m.r.number)}</span>` : ""}<span class="simname">${esc(m.r.horse)}</span></span></div>`).join("");
      const els = byNo.map((m) => [m, $(`[data-h="${CSS.escape(m.r.horse_key)}"]`, box)]);
      const W = () => box.clientWidth - 190, L = () => W() / 60;      // ~60 lengths visible across the track
      const at = (m, t) => { const e = Math.min(1, t / 0.55), late = Math.max(0, (t - 0.55) / 0.45), sm = late * late * (3 - 2 * late);
        const gap = early(m) * (1 - 0.35 * e) * (1 - sm) + fin(m) * sm; return Math.max(0, t * W() - gap * L()); };
      const line = $(".simfinish", box); line.style.left = (12 + W() + 12) + "px";     // where the winner's silk ends up
      $(".simlabels", box).style.width = (W() + 40) + "px";
      const paint = (t) => els.forEach(([m, d]) => { if (d) d.style.transform = `translateX(${at(m, t)}px)`; });
      if (still) return paint(1);
      const T = 7000, t0 = performance.now();
      const step = (now) => { const t = Math.min(1, (now - t0) / T); paint(t); if (t < 1 && box.isConnected) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }
    simControls();
    draw();
  }
  const mapKey = (r) => `${r.track}|${r.date}|${r.race}`;

  // upcoming field table (shared by meeting and race pages)
  const FIELD_HEAD = `<tr><th>No.</th><th class="name">Horse</th><th>Barrier</th><th>Weight</th><th>Jockey</th><th>Trainer</th><th>Last 10</th><th>Career</th><th>At Dist</th><th>On Going</th><th>Days</th><th>Blackbook</th></tr>`;
  function fieldRows(runs, history) {
    const b = book();
    return runs.map((r) => {
      const s = horseStats(history[r.horse_key] || [], r), scr = isScr(r);
      return `<tr style="${scr ? "opacity:.45;text-decoration:line-through" : ""}"><td><b>${dash(r.number)}</b>${Number(r.emergency) === 1 ? ' <span class="pill">EM</span>' : ""}</td>
        <td class="name">${horseCell(r)}${r.gear ? `<div class="mini">Gear: ${esc(r.gear)}</div>` : ""}</td><td>${dash(r.barrier)}</td><td>${wt(r)}</td>
        <td>${dash(r.jockey)}</td><td>${dash(r.trainer)}</td><td>${s.last10}</td><td>${s.career.text}</td><td>${s.dist.text}</td><td>${s.going.text}</td>
        <td>${s.daysSince ?? "1st"}</td><td><button class="star ${b[r.horse] ? "on" : ""}" data-h="${esc(r.horse)}" title="Blackbook">${b[r.horse] ? "★" : "☆"}</button></td></tr>`;
    }).join("");
  }
  function fieldStats(runs, history) {
    const live = runs.filter((r) => !isScr(r)).map((r) => ({ r, s: horseStats(history[r.horse_key] || [], r) }));
    const top = (label, f, fmt) => { const x = [...live].filter((e) => f(e) !== null).sort((a, b) => f(b) - f(a))[0];
      return `<div class="stat"><small>${label}</small><b style="font-size:16px">${x ? esc(x.r.horse) : "—"}</b><div class="mini">${x ? fmt(x) : ""}</div></div>`; };
    return `<div class="grid pad" style="margin:0">
      ${top("Most career wins", (e) => e.s.career.w, (e) => e.s.career.text)}
      ${top("Best win % (3+ starts)", (e) => e.s.career.n >= 3 ? e.s.career.win : null, (e) => e.s.career.win.toFixed(0) + "% · " + e.s.career.text)}
      ${top("Best at this distance", (e) => e.s.dist.n ? e.s.dist.w * 10 + e.s.dist.s * 3 + e.s.dist.t : null, (e) => e.s.dist.text)}
      ${top("Best on this going", (e) => e.s.going.n ? e.s.going.w * 10 + e.s.going.s * 3 + e.s.going.t : null, (e) => e.s.going.text)}
      ${top("Best at this track", (e) => e.s.track.n ? e.s.track.w * 10 + e.s.track.s * 3 + e.s.track.t : null, (e) => e.s.track.text)}
      ${top("Freshest (fewest days since run)", (e) => e.s.daysSince !== null ? -e.s.daysSince : null, (e) => e.s.daysSince + " days")}
    </div>`;
  }
  function bindStars(root, rerender) { $$(".star[data-h]", root).forEach((x) => x.onclick = () => { toggleBook(x.dataset.h); rerender(); }); }

  function raceSummary(runs) {
    const win = runs.find((r) => pos(r) === 1);
    const fav = [...runs].sort((a, b) => (num(a.starting_odds) ?? 999) - (num(b.starting_odds) ?? 999))[0];
    if (!win) return `<div class="pad note">No result recorded.</div>`;
    return `<div class="grid pad" style="margin:0">
      <div class="stat"><small>Winner</small><b style="font-size:17px">${esc(win.horse)}</b></div>
      <div class="stat"><small>Winning barrier</small><b>${dash(win.barrier)}</b></div>
      <div class="stat"><small>Winner's SP</small><b>${dash(win.starting_odds)}</b></div>
      <div class="stat"><small>Winning time</small><b>${runTime(win.finish_time)}</b></div>
      <div class="stat"><small>Favourite</small><b style="font-size:17px">${fav ? esc(fav.horse) + " (" + posLabel(fav) + ")" : "—"}</b></div>
      <div class="stat"><small>Second's margin</small><b>${dash((runs.find((r) => pos(r) === 2) || {}).margin)}${(runs.find((r) => pos(r) === 2) || {}).margin ? "L" : ""}</b></div>
    </div>`;
  }

  async function raceHistory(el, r) {
    if (!el) return;
    loading(el);
    try {
      const d = await get(`/api/runs?track=${encodeURIComponent(r.track)}&race_name=${encodeURIComponent(r.race_name)}&limit=2000`);
      const byDate = groupBy(d.runs.filter((x) => x.date !== r.date), (x) => x.date);
      const rows = Object.keys(byDate).sort().reverse().map((dt) => {
        const w = byDate[dt].find((x) => pos(x) === 1) || byDate[dt][0];
        return `<tr><td>${fmtDate(dt)}</td><td class="name">${horseCell(w)}</td><td>${dash(w.barrier)}</td><td>${dash(w.jockey)}</td><td>${dash(w.trainer)}</td><td>${dash(w.starting_odds)}</td><td>${runTime(w.finish_time)}</td><td><a href="${raceURL(w)}">Race →</a></td></tr>`;
      });
      el.innerHTML = rows.length ? `<div class="tablewrap"><table><thead><tr><th>Date</th><th class="name">Winner</th><th>Barrier</th><th>Jockey</th><th>Trainer</th><th>SP</th><th>Time</th><th></th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`
        : `<div class="pad note">No earlier runnings of "${esc(raceName(r.race_name))}" at ${esc(track(r.track).name)} in the database.</div>`;
    } catch (e) { fail(el, e); }
  }

  // horse name search box with suggestions; onPick(name)
  function horseSearch(input, box, onPick) {
    let timer, items = [], sel = -1;
    const close = () => { box.classList.add("hidden"); sel = -1; };
    const show = () => {
      box.innerHTML = items.map((h, i) => `<div data-i="${i}" class="${i === sel ? "on" : ""}"><span class="horsecell">${h.silk ? silk(h) : ""}${esc(h.horse)}</span><span class="mini">${h.starts ? `${h.starts} start${h.starts === 1 ? "" : "s"} · last ${fmtDate(h.last_date)}` : "first starter"}</span></div>`).join("")
        || `<div class="mini">No horses found</div>`;
      box.classList.remove("hidden");
      $$("[data-i]", box).forEach((x) => x.onmousedown = (e) => { e.preventDefault(); const h = items[Number(x.dataset.i)]; close(); onPick(h.horse); });
    };
    input.oninput = () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { close(); return; }
      timer = setTimeout(async () => { try { items = await get("/api/horses?q=" + encodeURIComponent(q)); sel = -1; show(); } catch (e) { close(); } }, 200);
    };
    input.onkeydown = (e) => {
      if (box.classList.contains("hidden") && e.key !== "Enter") return;
      if (e.key === "ArrowDown") { sel = Math.min(items.length - 1, sel + 1); show(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { sel = Math.max(0, sel - 1); show(); e.preventDefault(); }
      else if (e.key === "Enter") { const h = items[sel >= 0 ? sel : 0]; if (h) { close(); onPick(h.horse); } else if (input.value.trim()) onPick(input.value.trim()); e.preventDefault(); }
      else if (e.key === "Escape") close();
    };
    input.onblur = () => setTimeout(close, 150);
  }

  // ============================================================ PAGES
  const pages = {};

  // ---------------------------------------------- 1. Form Guide homepage
  pages["form-guide"] = async function () {
    let state = "ALL", data = null;
    const rows = $("#rows");
    async function load(date) {
      loading(rows);
      try {
        data = await get("/api/meetings" + (date ? "?date=" + date : ""));
        $("#date").value = data.date || "";
        history.replaceState(null, "", "?date=" + data.date);
        render();
      } catch (e) { fail(rows, e); }
    }
    function render() {
      const q = $("#q").value.toLowerCase();
      // results and upcoming fields for the same meeting can arrive under two names (WANG / Wangaratta): keep the results
      const all = data.meetings.map((m) => ({ ...m, t: track(m.track, m) }));
      const done = all.filter((m) => !m.upcoming);
      const same = (u, r) => nameKey(u.t.name) === nameKey(r.t.name)
        || (!TRACKS[String(r.track).toUpperCase()] && r.track.length >= 3 && nameKey(u.t.name).startsWith(String(r.track).toLowerCase().replace(/[^a-z]/g, "")));
      const list = all.filter((m) => !m.upcoming || !done.some((r) => r.t.aus === m.t.aus && same(m, r)))
        .filter((m) => state === "ALL" || (state === "INT" ? !m.t.aus : m.t.state === state))
        .filter((m) => (m.t.name + " " + m.track).toLowerCase().includes(q))
        .sort((a, b) => (b.t.aus - a.t.aus) || (TYPE_ORDER.indexOf(a.t.type) - TYPE_ORDER.indexOf(b.t.type)) || a.t.name.localeCompare(b.t.name));
      $("#count").textContent = list.length + " meetings · " + fmtDate(data.date, true) + (data.date === data.today ? " (today)" : "");
      rows.innerHTML = list.map((m) => `<tr><td class="name"><a href="${meetingURL(m.track, data.date)}">${esc(m.t.name)}</a> <span class="mini">${esc(m.t.show)}</span></td>
        <td>${esc(m.t.state) || "—"}</td><td>${esc(m.t.type) || "—"}</td><td>${m.races}</td><td>${m.runners}</td>
        <td>${esc(goingLabel(m)) || "—"}</td><td>${m.upcoming ? esc(fmtTime(m.first_race)) || "—" : '<span class="pill">Results</span>'}</td>
        <td><a class="btn" href="${meetingURL(m.track, data.date)}">${m.upcoming ? "Form Guide →" : "View Meeting →"}</a></td></tr>`).join("")
        || `<tr><td colspan="8">No meetings${data.meetings.length ? " match" : " on this date"}.</td></tr>`;
    }
    $$("#states button").forEach((b) => b.onclick = () => { $$("#states button").forEach((x) => x.classList.toggle("active", x === b)); state = b.dataset.state; render(); });
    $("#q").oninput = () => data && render();
    $("#date").onchange = () => load($("#date").value);
    $("#prev").onclick = () => data && data.prev && load(data.prev);
    $("#next").onclick = () => data && data.next && load(data.next);
    load(qs("date"));
  };

  // ---------------------------------------------- 2. Meeting
  pages["meeting"] = async function () {
    const t = qs("track"), d = qs("date");
    if (!t || !d) { $("#main").innerHTML = `<p class="sub">Choose a meeting from the <a href="form-guide.html">Form Guide</a>.</p>`; return; }
    $("#datecrumb").href = "form-guide.html?date=" + d;
    loading($("#runners"));
    let card;
    try { card = fixHistory(await get(`/api/card?track=${encodeURIComponent(t)}&date=${d}`)); } catch (e) { return fail($("#runners"), e); }
    const tr = track(t, card.runs[0]), up = card.upcoming;
    document.title = `${tr.name} ${fmtDate(d)} | The Sporting Almanac`;
    $("#trackname").textContent = tr.name; $("#trackcrumb").textContent = tr.name;
    $("#meta").textContent = [tr.state, tr.type, fmtDate(d, true), up ? "Upcoming" : "Results", card.runs[0] && card.runs[0].rail ? "Rail: " + card.runs[0].rail : ""].filter(Boolean).join(" · ");
    if (up) { $("#runners").closest("table").querySelector("thead").innerHTML = FIELD_HEAD; $$('[data-panel="stats"]').forEach((b) => b.textContent = "Field Stats"); }
    const races = groupBy(card.runs, (r) => r.race);
    const nums = Object.keys(races).map(Number).sort((a, b) => a - b);
    $("#m-races").textContent = nums.length; $("#m-runners").textContent = card.runs.filter((r) => !isScr(r)).length;
    if (up) { $("#m-first-box").classList.remove("hidden"); $("#m-first").textContent = fmtTime(card.runs.map((r) => r.start_time).filter(Boolean).sort()[0]) || "—"; }
    $("#m-going").textContent = goingLabel(card.runs[0] || {}) || "—";
    let active = Number(qs("race")) || nums[0];
    function setRace(n) {
      active = n;
      const runs = races[n], r0 = runs[0];
      $("#racebuttons").innerHTML = nums.map((x) => `<button class="${x === n ? "primary" : ""}" data-r="${x}">R${x}<small>${up ? esc(fmtTime(races[x][0].start_time)) : dash(races[x][0].distance) + "m"}</small></button>`).join("");
      $$("#racebuttons button").forEach((b) => b.onclick = () => { setRace(Number(b.dataset.r)); history.replaceState(null, "", `?track=${encodeURIComponent(t)}&date=${d}&race=${b.dataset.r}`); });
      $("#racelabel").textContent = "Race " + n + (up && r0.start_time ? " · " + fmtTime(r0.start_time) : "");
      $("#racelink").href = raceURL(r0);
      $("#racetitle").textContent = raceName(r0.race_name) || "Race " + n;
      $("#racedetails").textContent = [r0.distance && r0.distance + "m", r0.class || classLabel(r0),
        (up ? money(r0.prize_money) : money(runs.reduce((a, r) => a + (num(r.prize_money) || 0), 0))) + " prize money",
        runs.filter((r) => !isScr(r)).length + " runners", goingLabel(r0)].filter((x) => x && !x.startsWith("—")).join("  |  ");
      if (up) {
        const draw = () => { $("#runners").innerHTML = fieldRows(runs, card.history); bindStars($("#runners"), draw); };
        draw();
        speedMapEditor($('[data-tabcontent="speed"]'), runs, card.history, true, mapKey(r0));
        $('[data-tabcontent="stats"]').innerHTML = fieldStats(runs, card.history);
        $('[data-tabcontent="track"]').innerHTML = `<div class="pad"><p><b>${esc(tr.name)}</b> ${tr.state ? "· " + esc(tr.state) : ""} ${tr.type ? "· " + esc(tr.type) : ""}</p><p>Track condition: <b>${esc(goingLabel(r0) || "not yet rated")}</b></p>${r0.rail ? `<p>Rail: <b>${esc(r0.rail)}</b></p>` : ""}</div>`;
        raceHistory($('[data-tabcontent="history"]'), r0);
        return;
      }
      $("#runners").innerHTML = runs.map((r) => {
        const s = horseStats(card.history[r.horse_key] || [], r);
        return `<tr class="${pos(r) === 1 ? "win" : ""}"><td>${posLabel(r)}</td><td class="name">${horseCell(r)}</td><td>${dash(r.barrier)}</td><td>${dash(r.trainer)}</td><td>${dash(r.jockey)}</td><td>${dash(r.weight)}</td>
          <td>${s.last10}</td><td>${s.career.text}</td><td>${dash(r.starting_odds)}</td><td>${r.margin && pos(r) !== 1 ? r.margin + "L" : "—"}</td></tr>`;
      }).join("");
      speedMapEditor($('[data-tabcontent="speed"]'), runs, card.history, false, mapKey(r0));
      $('[data-tabcontent="stats"]').innerHTML = raceSummary(runs);
      $('[data-tabcontent="track"]').innerHTML = `<div class="pad"><p><b>${esc(tr.name)}</b> ${tr.state ? "· " + esc(tr.state) : ""} ${tr.type ? "· " + esc(tr.type) : ""}</p><p>Track condition: <b>${esc(goingLabel(r0) || "—")}</b></p><p class="note">Track code: ${esc(t)}</p></div>`;
      raceHistory($('[data-tabcontent="history"]'), r0);
    }
    $("#raceall").innerHTML = nums.map((n) => { const runs = races[n], r0 = runs[0], w = runs.find((r) => pos(r) === 1);
      return `<tr><td>${n}</td><td>${up ? esc(fmtTime(r0.start_time)) + " · " : ""}${dash(r0.distance)}m</td><td>${esc(classLabel(r0)) || "—"}</td><td class="name">${esc(raceName(r0.race_name))}</td><td>${runs.filter((r) => !isScr(r)).length}</td><td>${w ? esc(w.horse) : up ? "—" : "—"}</td><td><a href="${raceURL(r0)}">View Race →</a></td></tr>`; }).join("");
    if (up) $("#raceall").closest("table").querySelector("thead").innerHTML = `<tr><th>Race</th><th>Time · Distance</th><th>Class</th><th class="name">Race Name</th><th>Runners</th><th>Winner</th><th></th></tr>`;
    setRace(nums.includes(active) ? active : nums[0]);
    tabs("#meetingtabs");
  };

  // ---------------------------------------------- 3. Race
  pages["race"] = async function () {
    const t = qs("track"), d = qs("date"), n = Number(qs("race")) || 1;
    if (!t || !d) { $("#main").innerHTML = `<p class="sub">Choose a race from the <a href="form-guide.html">Form Guide</a>.</p>`; return; }
    $("#meetinglink").href = meetingURL(t, d);
    $("#rn").textContent = n; $("#comparelink").href = `comparison.html?track=${encodeURIComponent(t)}&date=${d}&race=${n}`;
    loading($("#field"));
    let card;
    try { card = fixHistory(await get(`/api/card?track=${encodeURIComponent(t)}&date=${d}&race=${n}`)); } catch (e) { return fail($("#field"), e); }
    const runs = card.runs, r0 = runs[0], tr = track(t, r0), up = card.upcoming;
    $("#meetinglink").textContent = tr.name;
    if (!r0) { $("#field").innerHTML = `<tr><td colspan="11">No race ${n} at ${esc(tr.name)} on ${fmtDate(d)}.</td></tr>`; return; }
    if (up) {
      document.title = `${raceName(r0.race_name) || "Race " + n} | The Sporting Almanac`;
      $("#rbadge").textContent = `Race ${n} · ${tr.name} · ${fmtDate(d, true)}${r0.start_time ? " · " + fmtTime(r0.start_time) : ""}`;
      $("#rtitle").textContent = raceName(r0.race_name) || "Race " + n;
      $("#rmeta").textContent = [r0.distance && r0.distance + "m", r0.class || classLabel(r0), money(r0.prize_money), goingLabel(r0), r0.rail && "Rail " + r0.rail].filter((x) => x && x !== "—").join(" · ");
      $("#field").closest("table").querySelector("thead").innerHTML = FIELD_HEAD;
      const draw = () => { $("#field").innerHTML = fieldRows(runs, card.history); bindStars($("#field"), draw); };
      draw();
      speedMapEditor($('[data-tabcontent="speed"]'), runs, card.history, true, mapKey(r0));
      $$('[data-panel="stats"]').forEach((b) => b.textContent = "Field Stats");
      $('[data-tabcontent="stats"]').innerHTML = fieldStats(runs, card.history);
      $('[data-tabcontent="sectionals"]').innerHTML = `<div class="pad note">Positions in running appear here after the race.</div>`;
      raceHistory($('[data-tabcontent="history"]'), r0);
      tabs("#racetabs");
      return;
    }
    document.title = `${raceName(r0.race_name) || "Race " + n} | The Sporting Almanac`;
    $("#rbadge").textContent = `Race ${n} · ${tr.name} · ${fmtDate(d, true)}`;
    $("#rtitle").textContent = raceName(r0.race_name) || "Race " + n;
    $("#rmeta").textContent = [r0.distance && r0.distance + "m", r0.class || classLabel(r0), money(runs.reduce((a, r) => a + (num(r.prize_money) || 0), 0)), goingLabel(r0)].filter((x) => x && x !== "—").join(" · ");
    function render() {
      const b = book();
      $("#field").innerHTML = runs.map((r) => {
        const s = horseStats(card.history[r.horse_key] || [], r);
        return `<tr class="${pos(r) === 1 ? "win" : ""}"><td>${posLabel(r)}</td><td class="name">${horseCell(r)}</td><td>${dash(r.barrier)}</td><td>${dash(r.weight)}</td><td>${dash(r.jockey)}</td><td>${dash(r.trainer)}</td>
          <td>${s.last5}</td><td>${s.career.text}</td><td>${s.dist.text}</td><td>${dash(r.starting_odds)}</td>
          <td><button class="star ${b[r.horse] ? "on" : ""}" data-h="${esc(r.horse)}" title="Blackbook">${b[r.horse] ? "★" : "☆"}</button></td></tr>`;
      }).join("");
      $$("#field .star").forEach((x) => x.onclick = () => { toggleBook(x.dataset.h); render(); });
    }
    render();
    speedMapEditor($('[data-tabcontent="speed"]'), runs, card.history, false, mapKey(r0));
    $('[data-tabcontent="stats"]').innerHTML = raceSummary(runs);
    $('[data-tabcontent="sectionals"]').innerHTML = `<div class="tablewrap"><table><thead><tr><th>Pos</th><th class="name">Horse</th><th>1200m</th><th>800m</th><th>400m</th><th>Finish</th><th>Time</th><th>Margin</th></tr></thead><tbody>${runs.map((r) =>
      `<tr><td>${posLabel(r)}</td><td class="name">${horseCell(r)}</td><td>${dash(r.pos_1200)}</td><td>${dash(r.pos_800)}</td><td>${dash(r.pos_400)}</td><td>${dash(pos(r))}</td><td>${runTime(r.finish_time)}</td><td>${r.margin && pos(r) !== 1 ? r.margin + "L" : "—"}</td></tr>`).join("")}</tbody></table></div>
      <p class="pad note">Positions in running at each point of the race. Split times aren't in the data.</p>`;
    raceHistory($('[data-tabcontent="history"]'), r0);
    tabs("#racetabs");
  };

  // ---------------------------------------------- 4. Horse profile
  pages["horse"] = async function () {
    const name = qs("horse");
    horseSearch($("#hsearch"), $("#hsuggest"), (h) => location.href = horseURL(h));
    if (!name) {
      $$("#main > :not(.crumb):not(.controls)").forEach((el) => el.classList.add("hidden"));
      $("#hsearch").focus();
      return;
    }
    $("#horseName").textContent = name.toUpperCase();
    loading($("#formrows"));
    let runs, entries = [];
    try {
      [runs, entries] = await Promise.all([get(`/api/runs?horse=${encodeURIComponent(name)}&limit=5000`).then((x) => x.runs), get(`/api/upcoming?horse=${encodeURIComponent(name)}`).catch(() => [])]);
    } catch (e) { return fail($("#formrows"), e); }
    // more than one horse with this name? show the one asked for (c=country) and offer the others
    const groups = horseGroups(runs);
    if (groups.length > 1) {
      const want = qs("c").toUpperCase(), wantRg = want === "NZ" ? "ANZ" : want === "IRE" || want === "GBR" ? "GBI" : want;
      const e0 = entries.find((e) => !isScr(e));
      const wantT = qs("t").toLowerCase();
      let g = groups.find((x) => x.id === want)
        || (wantT && groups.find((x) => x.runs.some((r) => trainerKeys(r.trainer).includes(wantT)) && (!want || x.regions.has(wantRg) || x.regions.has(want))))
        || (want && groups.find((x) => x.regions.has(wantRg) || x.regions.has(want)))
        || (e0 && groups.find((x) => x.runs.includes(sameHorse(runs, e0)[0]))) || groups[0];
      runs = g.runs;
      entries = entries.filter((e) => g.regions.has(regionOf(e)) || trainerKeys(e.trainer).some((k) => g.runs.some((r) => trainerKeys(r.trainer).includes(k))));
      if (!g.regions.has("ANZ")) runs = runs.map((r) => ({ ...r, silk: null }));   // the silks folder is Australian horses
      const nm = groups[0].latest.horse.replace(/\s*\([A-Z]{2,4}\)\s*$/, "");
      const box = document.createElement("div");
      box.className = "twins";
      box.innerHTML = `<b>${groups.length} horses are called ${esc(nm)}.</b> Showing: ` + groups.map((x) =>
        `<a class="filter${x === g ? " active" : ""}" href="horse.html?horse=${encodeURIComponent(qs("horse"))}&c=${x.id}">${esc(nm)} (${esc(x.country)}) · ${esc(dash(x.latest.trainer))} · ${x.runs.length} start${x.runs.length === 1 ? "" : "s"}</a>`).join(" ");
      $(".hero").before(box);
    }
    $('[data-tabcontent="entries"]').innerHTML = `<h3>Upcoming Entries</h3>` + (entries.length ? `<div class="tablewrap"><table><thead><tr><th>Date</th><th>Time</th><th>Track</th><th class="name">Race</th><th>Dist</th><th>No.</th><th>Barrier</th><th>Weight</th><th>Jockey</th></tr></thead><tbody>${entries.map((e) =>
      `<tr style="${isScr(e) ? "opacity:.45;text-decoration:line-through" : ""}"><td>${fmtDate(e.date)}</td><td>${esc(fmtTime(e.start_time))}</td><td>${esc(track(e.track, e).name)}</td><td class="name"><a href="${raceURL(e)}">${esc(raceName(e.race_name)) || "Race " + e.race}</a></td><td>${dash(e.distance)}</td><td>${dash(e.number)}</td><td>${dash(e.barrier)}</td><td>${wt(e)}</td><td>${dash(e.jockey)}</td></tr>`).join("")}</tbody></table></div>`
      : `<p class="note">No upcoming starts in the next few days.</p>`);
    if (entries.length) { const b = $('[data-panel="entries"]'); if (b) b.textContent = `Entries (${entries.length})`; }
    const next = entries.find((e) => !isScr(e)) || entries[0];
    const star = (disp) => { const on = !!book()[disp]; $("#star").textContent = on ? "★" : "☆"; $("#star").classList.toggle("on", on); };
    if (!runs.length) {
      $("#formrows").innerHTML = `<tr><td colspan="19">${entries.length ? "No starts yet — see Entries for its first run." : "No runs found for " + esc(name) + "."}</td></tr>`;
      if (next) {
        const disp = next.horse;
        document.title = `${disp} | The Sporting Almanac`;
        $("#horseName").textContent = disp.toUpperCase();
        $("#silk").innerHTML = silk(next, true);
        $("#trainerlabel").textContent = "Trainer";
        $("#trainer").textContent = dash(next.trainer);
        $("#star").onclick = () => { toggleBook(disp); star(disp); }; star(disp);
        const first = `<p class="note">First starter — no race record yet.</p>`;
        $("#m-dist").textContent = next.distance ? next.distance + "m" : "—";
        $(".metric:nth-child(4) small") && ($(".metric:nth-child(4) small").textContent = "Next Start Distance");
        ["#c-starts", "#c-w", "#c-s", "#c-t"].forEach((x) => $(x).textContent = "0");
        $("#winrange").textContent = "—"; $("#goingrec").innerHTML = first; $("#fresh").innerHTML = first;
        $("#lastcmp").closest(".panel").querySelector("h3").textContent = "Next Start";
        $("#lastcmp").innerHTML = `<p><a href="${raceURL(next)}">${fmtDate(next.date)} ${esc(fmtTime(next.start_time))} · ${esc(track(next.track, next).name)} R${next.race}</a></p>
          <p>${esc(raceName(next.race_name))}</p><p>${dash(next.distance)}m · Barrier <b>${dash(next.barrier)}</b> · ${wt(next)}kg</p><p>Jockey: <b>${esc(dash(next.jockey))}</b></p>`;
        $$('[data-panel="entries"]').forEach((b) => b.click());
      }
      tabs("#horsetabs"); if (next) $$('#horsetabs [data-panel="entries"]').forEach((b) => b.click());
      return;
    }
    runs.sort((a, b) => b.date.localeCompare(a.date) || 0);
    const last = runs[0], prev = runs[1], disp = last.horse;
    document.title = `${disp} | The Sporting Almanac`;
    $("#horseName").textContent = disp.toUpperCase();
    $("#silk").innerHTML = silk(last.silk ? last : next || last, true);
    // current trainer: from the next start's field if there is one, else the last start
    if (next && next.trainer) { $("#trainerlabel").textContent = "Trainer"; $("#trainer").textContent = next.trainer; }
    else $("#trainer").textContent = dash(last.trainer);
    $("#star").onclick = () => { toggleBook(disp); star(disp); }; star(disp);

    const lastWin = runs.find((r) => pos(r) === 1);
    $("#m-run").textContent = days(last.date, todayISO());
    $("#m-win").textContent = lastWin ? days(lastWin.date, todayISO()) : "—";
    $("#m-weight").textContent = last.weight ? last.weight + "kg" : "—";
    $("#m-dist").textContent = last.distance ? last.distance + "m" : "—";
    $("#m-class").textContent = classLabel(last) || "—";

    const c = record(runs);
    $("#c-starts").textContent = c.n; $("#c-w").textContent = c.w; $("#c-s").textContent = c.s; $("#c-t").textContent = c.t;
    $("#c-pct").textContent = `Win ${c.win.toFixed(1)}% · Place ${c.place.toFixed(1)}%`;
    const wins = runs.filter((r) => pos(r) === 1 && dist(r));
    $("#winrange").textContent = wins.length ? `${Math.min(...wins.map(dist))}–${Math.max(...wins.map(dist))}m` : "no wins yet";
    $("#goingrec").innerHTML = ["Good", "Soft", "Heavy", "Synthetic", "Firm"].map((g) => [g, record(runs.filter((r) => going(r) === g))])
      .filter(([, r]) => r.n).map(([g, r]) => `<p>${g}: <b>${r.text}</b></p>`).join("") || "<p>—</p>";
    const s = horseStats(runs.slice(1), last), tags = upTags(runs);
    $("#fresh").innerHTML = `<p>First-up: <b>${record(runs.filter((r) => tags.get(r) === 1)).text}</b></p><p>Second-up: <b>${record(runs.filter((r) => tags.get(r) === 2)).text}</b></p>
      <p>${esc(track(last.track).name)}: <b>${record(runs.filter((r) => r.track === last.track)).text}</b></p>
      <p>${esc(track(last.track).name)} ${dash(last.distance)}m: <b>${record(runs.filter((r) => r.track === last.track && near(dist(r), dist(last)))).text}</b></p>`;
    $("#lastcmp").innerHTML = `<p>${esc(dash(last.jockey))} on this horse: <b>${record(runs.filter((r) => r.jockey && r.jockey === last.jockey)).text}</b></p>
      ${prev ? `<p>Weight change: <b>${fmtDelta(num(last.weight), num(prev.weight), "kg")}</b></p><p>Distance change: <b>${fmtDelta(dist(last), dist(prev), "m")}</b></p>
      <p>Class: <b>${classLabel(prev) && classLabel(last) && classLabel(prev) !== classLabel(last) ? esc(classLabel(prev) + " → " + classLabel(last)) : "same"}</b></p>` : "<p>First start.</p>"}
      <p>Days between last two runs: <b>${prev ? days(prev.date, last.date) : "—"}</b></p>`;

    let scope = "all", avgs = null;
    get("/api/avgtimes?tracks=" + encodeURIComponent([...new Set(runs.map((r) => String(r.track).toUpperCase()))].join(","))).then((x) => { avgs = x; renderForm(); }).catch(() => {});
    function renderForm() {
      const list = runs.filter((r) => scope === "all" || (scope === "aus" ? track(r.track).aus : !track(r.track).aus));
      $("#formrows").innerHTML = list.map((r) => {
        const i = runs.indexOf(r), p = runs[i + 1];
        return `<tr class="${pos(r) === 1 ? "win" : ""}"><td>${fmtDate(r.date)}</td><td><a href="${meetingURL(r.track, r.date)}">${esc(track(r.track).name)}</a></td>
          <td class="name"><a href="${raceURL(r)}">${esc(raceName(r.race_name)) || "Race " + r.race}</a></td><td>${dash(r.distance)}</td><td>${esc(goingLabel(r)) || "—"}</td><td>${esc(classLabel(r)) || "—"}</td>
          <td><b>${posLabel(r)}</b>${r.starters ? `<span class="mini">/${esc(r.starters)}</span>` : ""}</td><td>${r.margin && pos(r) !== 1 ? r.margin + "L" : "—"}</td><td>${dash(r.barrier)}</td><td>${dash(r.weight)}</td>
          <td>${dash(r.jockey)}</td><td>${dash(r.starting_odds)}</td><td>${runTime(r.finish_time)}</td>${avgs ? vsAverage(r, avgs) : `<td class="mini">…</td>`}<td>${dash(r.pos_400)}</td><td>${dash(r.pos_800)}</td>
          <td>${p ? fmtDelta(num(r.weight), num(p.weight), "") : "—"}</td><td>${p ? fmtDelta(dist(r), dist(p), "") : "—"}</td>
          <td>${p && classLabel(p) !== classLabel(r) ? esc(classLabel(p) + " → " + classLabel(r)) : "—"}</td></tr>`;
      }).join("") || `<tr><td colspan="19">No ${scope === "aus" ? "Australian" : "international"} runs.</td></tr>`;
    }
    $$("[data-scope]").forEach((b) => b.onclick = () => { $$("[data-scope]").forEach((x) => x.classList.toggle("active", x === b)); scope = b.dataset.scope; renderForm(); });
    renderForm();

    // Stats tab: records by distance band, going, track, jockey
    const band = (r) => { const x = dist(r); return !x ? "?" : x <= 1100 ? "Up to 1100m" : x <= 1300 ? "1101–1300m" : x <= 1600 ? "1301–1600m" : x <= 2000 ? "1601–2000m" : x <= 2400 ? "2001–2400m" : "2401m+"; };
    const table = (title, groups) => `<h3>${title}</h3><div class="tablewrap" style="margin-bottom:18px"><table><thead><tr><th class="name"></th><th>Record</th><th>Win %</th><th>Place %</th></tr></thead><tbody>${Object.entries(groups)
      .map(([k, v]) => [k, record(v)]).sort((a, b) => b[1].n - a[1].n).map(([k, r]) => `<tr><td class="name">${esc(k)}</td><td>${r.text}</td><td>${r.win.toFixed(0)}%</td><td>${r.place.toFixed(0)}%</td></tr>`).join("")}</tbody></table></div>`;
    $('[data-tabcontent="stats"]').innerHTML = table("By distance", groupBy(runs, band)) + table("By going", groupBy(runs, (r) => going(r) || "Unknown"))
      + table("By track", groupBy(runs, (r) => track(r.track).name)) + table("By jockey", groupBy(runs.filter((r) => r.jockey), (r) => r.jockey));
    tabs("#horsetabs");
  };
  function fmtDelta(a, b, unit) { if (a === null || b === null) return "—"; const d = Math.round((a - b) * 10) / 10; return d === 0 ? "0" : (d > 0 ? "+" : "−") + Math.abs(d) + unit; }

  // ---------------------------------------------- 5. Comparison
  pages["comparison"] = async function () {
    const t = qs("track"), d = qs("date"), n = Number(qs("race")) || 1;
    if (!t || !d) { $("#main").innerHTML = `<p class="sub">Open a race and choose <b>Compare runners</b>.</p>`; return; }
    $("#racelink").href = `race.html?track=${encodeURIComponent(t)}&date=${d}&race=${n}`;
    loading($("#compbody"));
    let card;
    try { card = fixHistory(await get(`/api/card?track=${encodeURIComponent(t)}&date=${d}&race=${n}`)); } catch (e) { return fail($("#compbody"), e); }
    const runs = card.runs.filter((r) => !isScr(r)), up = card.upcoming, tr = track(t, runs[0]);
    $("#racelink").textContent = `${tr.name} Race ${n}`;
    if (!runs.length) { $("#compbody").innerHTML = `<tr><td>No such race.</td></tr>`; return; }
    $("#racehead").textContent = `${tr.name} · ${fmtDate(d, true)} · Race ${n} · ${raceName(runs[0].race_name)} (${dash(runs[0].distance)}m)`;
    const stats = new Map(runs.map((r) => [r, horseStats(card.history[r.horse_key] || [], r)]));
    let selected = up ? [...runs].sort((a, b) => stats.get(b).career.win - stats.get(a).career.win).slice(0, 4)
      : [...runs].sort((a, b) => (num(a.starting_odds) ?? 999) - (num(b.starting_odds) ?? 999)).slice(0, 4);
    $("#horses").innerHTML = runs.map((r, i) => `<option value="${i}">${esc(r.horse)}</option>`).join("");
    const rowsDef = [
      ["Silk", (r) => silk(r, true)], up ? ["Number", (r) => `<b>${dash(r.number)}</b>`] : ["Finished", (r) => `<b>${posLabel(r)}</b>`], ["Barrier", (r) => dash(r.barrier)], ["Weight", (r) => wt(r)],
      ["Jockey", (r) => dash(r.jockey)], ["Trainer", (r) => dash(r.trainer)], up ? ["Gear changes", (r) => dash(r.gear)] : ["Starting price", (r) => dash(r.starting_odds)],
      ["Recent form", (r) => stats.get(r).last10], ["Career", (r) => stats.get(r).career.text], ["At this distance", (r) => stats.get(r).dist.text],
      ["On this going", (r) => stats.get(r).going.text], ["At this track", (r) => stats.get(r).track.text], ["With this jockey", (r) => stats.get(r).jockey.text],
      ["First-up / second-up", (r) => stats.get(r).firstUp.text + " / " + stats.get(r).secondUp.text], ["Days since last run", (r) => dash(stats.get(r).daysSince)],
      ["Last start", (r) => { const l = stats.get(r).last; return l ? `${posLabel(l)} · ${esc(track(l.track).name)} ${dash(l.distance)}m · ${fmtDate(l.date)}` : "First start"; }],
    ];
    function comp() {
      $("#comphead").innerHTML = "<tr><th>Metric</th>" + selected.map((r) => `<th><a href="${horseURL(r.horse, r)}">${esc(r.horse)}</a> <button data-x="${runs.indexOf(r)}" title="Remove">×</button></th>`).join("") + "</tr>";
      $("#compbody").innerHTML = rowsDef.map(([l, f]) => `<tr><td>${l}</td>${selected.map((r) => `<td>${f(r)}</td>`).join("")}</tr>`).join("");
      $$("#comphead [data-x]").forEach((b) => b.onclick = () => { selected = selected.filter((r) => r !== runs[Number(b.dataset.x)]); comp(); });
    }
    $("#add").onclick = () => { const r = runs[Number($("#horses").value)]; if (!selected.includes(r)) selected.push(r); comp(); };
    comp();
  };

  // ---------------------------------------------- 6. Blackbook
  pages["blackbook"] = async function () {
    horseSearch($("#search"), $("#suggest"), (h) => { const b = book(); b[h] ??= { note: "", added: todayISO() }; saveBook(b); $("#search").value = ""; render(); });

    const lastRuns = {};
    async function render() {
      const b = book(), names = Object.keys(b).sort();
      $("#count").innerHTML = esc(names.length + (names.length === 1 ? " horse" : " horses")) + (loggedIn() ? ` · saved to your account`
        : ` · saved in this browser only — <a href="#" id="bblogin">log in</a> to keep it on every device`);
      const bl = $("#bblogin"); if (bl) bl.onclick = (e) => { e.preventDefault(); signIn("login"); };
      $("#bookrows").innerHTML = names.map((h) => `<tr><td class="name" data-last="${esc(h)}"><span class="horsecell"><span class="silk none"></span><a href="${horseURL(h)}">${esc(h)}</a></span></td>
        <td><input class="field blacknote" value="${esc(b[h].note || "")}" data-note="${esc(h)}" placeholder="Add a note…"></td>
        <td data-next="${esc(horseKey(h))}" class="mini">—</td><td data-lastrun="${esc(h)}" class="mini">…</td><td><button data-remove="${esc(h)}">Remove</button></td></tr>`).join("")
        || `<tr><td colspan="5">No horses saved yet. Search above, or tap ☆ on any race or horse page.</td></tr>`;
      if (names.length) get("/api/upcoming?keys=" + encodeURIComponent(names.map(horseKey).join(","))).then((list) => {
        for (const e of list) {
          const cell = $$("[data-next]").find((x) => x.dataset.next === e.horse_key);
          if (cell && cell.textContent === "—") cell.innerHTML = `<a href="${raceURL(e)}"><b>${fmtDate(e.date)} ${esc(fmtTime(e.start_time))}</b> · ${esc(track(e.track, e).name)} R${e.race} · ${dash(e.distance)}m${e.barrier ? " · b" + esc(e.barrier) : ""}</a>${isScr(e) ? " (scratched)" : ""}`;
        }
      }).catch(() => {});
      $$("[data-note]").forEach((el) => el.onchange = () => { const b = book(); if (b[el.dataset.note]) { b[el.dataset.note].note = el.value; saveBook(b); } });
      $$("[data-remove]").forEach((el) => el.onclick = () => { const b = book(); delete b[el.dataset.remove]; saveBook(b); render(); });
      for (const h of names) {
        try {
          const r = lastRuns[h] ||= (await get(`/api/runs?horse=${encodeURIComponent(h)}&limit=1`)).runs[0] || null;
          const cell = $$("[data-lastrun]").find((x) => x.dataset.lastrun === h), nameCell = $$("[data-last]").find((x) => x.dataset.last === h);
          if (cell) cell.innerHTML = r ? `<a href="${raceURL(r)}">${posLabel(r)} · ${esc(track(r.track).name)} R${r.race} · ${dash(r.distance)}m · ${fmtDate(r.date)}</a>` : "No runs found";
          if (nameCell && r) nameCell.querySelector(".silk").outerHTML = silk(r);
        } catch (e) { /* leave as is */ }
      }
    }
    render();
  };

  // ------------------------------------------------------------ start
  window.FG = { track, record, figure, horseStats, API };
  document.addEventListener("DOMContentLoaded", async () => {
    accountUI();
    await Promise.race([syncBook(), new Promise((r) => setTimeout(r, 3000))]);
    accountUI();                                        // in case the sign-in had expired
    if (/^[0-9a-f]{64}$/i.test(resetToken)) signIn("reset");   // arrived from a password-reset email
    const p = document.body.dataset.page;
    if (pages[p]) pages[p]().catch((e) => console.error(e));
  });
})();
