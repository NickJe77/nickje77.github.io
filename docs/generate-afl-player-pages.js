// generate-afl-player-pages.js
//
// Reads every docs/data/afl/afl_<year>.json file, groups every match
// appearance by player, and writes one static HTML page per player:
// afl-player-<slug>.html (or afl-player-<slug>-<team>.html for the
// handful of shared-name players split by DISAMBIG_GROUPS below).
//
// Run from inside docs/, e.g.:  node generate-afl-player-pages.js

const fs = require("fs");
const path = require("path");

const START_YEAR = 1965;
const END_YEAR = 2026;
const DATA_DIR = path.join(__dirname, "data", "afl");
const OUTPUT_DIR = path.join(__dirname, "out-players");

// ---- Same normalisation rules as the live afl-player.html page ----
const DISAMBIG_GROUPS = {
  "Will Hayes": [["Western Bulldogs", "Carlton"], ["Collingwood"]],
  "Josh Kennedy": [["West Coast", "Carlton"], ["Sydney", "Hawthorn"]],
  "Tom Lynch": [["St Kilda", "Adelaide"], ["Gold Coast", "Richmond"]],
  // Added after a full-dataset audit found head-to-head matches proving
  // these are two different real players sharing a name (e.g. Scott
  // Thompson: North Melbourne and Adelaide appear against EACH OTHER in
  // nearly every round from 2008-2017 -- a decade of two concurrent
  // careers, not a data error).
  "Mitchell Brown": [["West Coast"], ["Geelong", "Essendon"]],
  "Scott Thompson": [["Melbourne", "Adelaide"], ["North Melbourne"]],
};
const PLAYER_NAME_ALIASES = {
  "Luke D-Uniacke": "Luke Davies-Uniacke",
  "Cooper D-Tytler": "Cooper Duff-Tytler",
  // "Bailey Williams": "Bailey J. Williams" REMOVED -- confirmed WRONG:
  // two different real players (Western Bulldogs vs West Coast), proven
  // by a head-to-head match between them on 2026-07-12 with different
  // stat lines. This alias silently merged two separate careers into
  // one static page since 2020.
};
const TEAM_NAME_CANONICAL = {
  "footscray": "Western Bulldogs",
  "south melbourne": "Sydney",
  "brisbane bears": "Brisbane",
  "kangaroos": "North Melbourne",
};
const ROUND_NAME_CANONICAL = {
  "ef": "Elimination Final", "round ef": "Elimination Final", "elimination final": "Elimination Final",
  "sf": "Semi Final", "round sf": "Semi Final", "semi final": "Semi Final",
  "qf": "Qualifying Final", "round qf": "Qualifying Final", "qualifying final": "Qualifying Final",
  "pf": "Preliminary Final", "round pf": "Preliminary Final", "preliminary final": "Preliminary Final",
  "gf": "Grand Final", "round gf": "Grand Final", "grand final": "Grand Final",
};

function normaliseDashes(str) { return str ? str.replace(/[\u2013\u2014]/g, "-") : str; }
function normaliseName(str) {
  if (!str) return str;
  str = normaliseDashes(str);
  str = str.replace(/\u2019/g, "'");
  str = str.replace(/\bO([A-Z][a-z])/g, "O'$1");
  return str;
}
function normaliseTeam(t) {
  if (!t) return t;
  const dashed = normaliseDashes(t).trim();
  return TEAM_NAME_CANONICAL[dashed.toLowerCase()] || dashed;
}
function normaliseRound(r) {
  if (!r) return r;
  const key = r.trim().toLowerCase();
  return ROUND_NAME_CANONICAL[key] || r.trim();
}
function normaliseGame(g) {
  if (g.player) g.player = normaliseName(g.player);
  if (g.played_for) g.played_for = normaliseTeam(g.played_for);
  if (g.played_against) g.played_against = normaliseTeam(g.played_against);
  if (g.home_team) g.home_team = normaliseTeam(g.home_team);
  if (g.away_team) g.away_team = normaliseTeam(g.away_team);
  if (g.round) g.round = normaliseRound(g.round);
  if (g.player === "Gary Ablett" && g.season >= 2000) g.player = "Gary Ablett Jnr";
  if (g.player === "Bailey Williams" && g.played_for === "West Coast") g.player = "Bailey J. Williams";
  if (g.player && PLAYER_NAME_ALIASES[g.player]) g.player = PLAYER_NAME_ALIASES[g.player];
  return g;
}
// FIX (found after the static pages were reported as still wrong even
// after the live afl-player.html and season data were fixed): this
// generator had its own copy of dedupeGames, made once on 2026-08-23 and
// never updated since -- it never received any of the later fixes. It
// only matched on season+round+played_for+played_against, with no score
// or stat check, so it didn't correctly separate a drawn Grand Final from
// its replay, and (more importantly) didn't recognize a blank-round
// "Season Player Rankings" junk row as a duplicate of an already-labeled
// game, letting it survive as a permanent phantom row baked into the
// static HTML. This is the same corrected logic now used live: match on
// the player's own stat line (always present, unlike team score) as the
// fingerprint for "is this the same match", and drop a blank-round row
// when a labeled sibling with the same fingerprint exists.
function dedupeGames(games) {
  const statFingerprint = g =>
    (g.D||0)+"_"+(g.G||0)+"_"+(g.B||0)+"_"+(g.BR||0)+"_"+(g.K||0)+"_"+(g.HB||0);
  const matchKeyOf = g =>
    g.season + "__" + g.played_for + "__" + g.played_against + "__" + statFingerprint(g);

  const hasLabeledRound = new Set();
  games.forEach(g => { if (g.round) hasLabeledRound.add(matchKeyOf(g)); });

  const seen = new Set(), out = [];
  games.forEach(g => {
    if (!g.round && hasLabeledRound.has(matchKeyOf(g))) return;
    const key = g.season + "__" + g.round + "__" + g.played_for + "__" + g.played_against + "__" + statFingerprint(g);
    if (seen.has(key)) return;
    seen.add(key);
    out.push(g);
  });
  return out;
}
function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function slugify(str) {
  return String(str)
    .toLowerCase()
    .replace(/'/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// ---- 1. Load every season file, normalise every row ----
let allGames = [];
for (let year = START_YEAR; year <= END_YEAR; year++) {
  const file = path.join(DATA_DIR, `afl_${year}.json`);
  if (!fs.existsSync(file)) continue;
  const rows = JSON.parse(fs.readFileSync(file, "utf8"));
  rows.forEach(r => allGames.push(normaliseGame({ ...r, season: year })));
}
console.log(`Loaded ${allGames.length} player-game rows across all seasons.`);

// ---- 2. Group by player name ----
const byPlayer = {};
allGames.forEach(g => {
  if (!g.player) return;
  if (!byPlayer[g.player]) byPlayer[g.player] = [];
  byPlayer[g.player].push(g);
});

// ---- 3. Split disambiguation groups into separate identities ----
// Produces a list of { slugSuffix, label, games } per player name.
function splitIntoIdentities(name, games) {
  if (!DISAMBIG_GROUPS[name]) {
    return [{ label: name, games }];
  }
  return DISAMBIG_GROUPS[name].map(teamGroup => ({
    label: `${name} (${teamGroup.join("/")})`,
    slugSuffix: "-" + slugify(teamGroup[0]),
    games: games.filter(g => teamGroup.includes(g.played_for)),
  })).filter(identity => identity.games.length > 0);
}

// ---- 4. Build one page per identity ----
function gameLink(g) {
  return `afl-game.html?year=${g.season}&home=${encodeURIComponent(g.home_team)}&away=${encodeURIComponent(g.away_team)}&round=${encodeURIComponent(g.round)}`;
}

function buildCareerStats(games) {
  const n = games.length;
  const sum = key => games.reduce((a, g) => a + (+g[key] || 0), 0);
  const avg = key => n ? (sum(key) / n).toFixed(1) : "0.0";
  const teams = [...new Set(games.map(g => g.played_for))];
  const seasons = games.map(g => +g.season);
  return {
    games: n,
    teams,
    firstSeason: Math.min(...seasons),
    lastSeason: Math.max(...seasons),
    totalD: sum("D"), avgD: avg("D"),
    totalG: sum("G"), avgG: avg("G"),
    totalB: sum("B"), avgB: avg("B"),
    totalBR: sum("BR"),
  };
}

function renderGameRows(games) {
  const sorted = [...games].sort((a, b) => a.season - b.season);
  return sorted.map(g => `
      <tr onclick="location.href='${gameLink(g)}'">
        <td>${g.season}</td>
        <td>${escapeHtml(g.round)}</td>
        <td class="left">${escapeHtml(g.played_for)}</td>
        <td>${escapeHtml(g.played_against)}</td>
        <td>${g.D || 0}</td>
        <td>${g.G || 0}</td>
        <td>${g.B || 0}</td>
        <td>${g.BR || 0}</td>
      </tr>`).join("");
}

function buildPage(label, slug, games) {
  const dedup = dedupeGames(games);
  const stats = buildCareerStats(dedup);
  const title = `${label} — AFL Career Stats & Game Log | The Sporting Almanac`;
  const description = `${label}: ${stats.games} AFL games (${stats.firstSeason}–${stats.lastSeason}) for ${stats.teams.join(", ")}. Full career disposals, goals, behinds and Brownlow vote history.`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<script src="/js/analytics.js"></script>
<meta charset="UTF-8">
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}">
<link rel="canonical" href="https://thesportingalmanac.com/afl-player-${slug}.html">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#eceff3;--surface:#fff;--ink:#0f141a;--muted:#69727c;--line:#e3e8ee;--board:#0c130f;--board-2:#161f16;--accent:#c99a3d;--display:'Oswald',system-ui,sans-serif;--body:'Inter',system-ui,sans-serif;--radius:16px;}
*{box-sizing:border-box;}
body{font-family:var(--body);margin:0;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;}
.navbar{display:flex;justify-content:center;gap:26px;padding:15px;background:#fff;border-bottom:1px solid var(--line);font-weight:600;font-size:14px;}
.navbar a{text-decoration:none;color:var(--ink);opacity:.7;}
.navbar a.current{opacity:1;color:var(--accent);}
.page{max-width:1180px;margin:0 auto;padding:26px 20px 70px;}
.hero{background:linear-gradient(160deg,var(--board-2),var(--board));border-radius:var(--radius);color:#fff;padding:22px 26px 26px;margin-bottom:20px;}
.eyebrow{font-size:11.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:8px;}
h1{margin:0;font-family:var(--display);font-weight:600;font-size:clamp(22px,4vw,34px);text-transform:uppercase;color:#fff;}
.hero p{margin:10px 0 0;color:rgba(255,255,255,.7);font-size:14px;}
#summary{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:22px 24px;margin-bottom:20px;}
.section-title{margin:0 0 10px;font-family:var(--display);font-weight:600;color:var(--muted);text-transform:uppercase;font-size:12.5px;letter-spacing:.1em;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;}
.stat-box{border:1px solid var(--line);border-radius:var(--radius);padding:16px 12px;text-align:center;}
.stat-box strong{display:block;font-family:var(--display);font-weight:600;font-size:24px;margin-bottom:4px;}
.stat-box span{font-size:12px;color:var(--muted);font-weight:600;text-transform:uppercase;}
.table-wrap{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);}
table{border-collapse:collapse;width:100%;font-size:13px;}
th,td{padding:9px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
th{background:#f7f9fb;font-weight:600;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);}
td.left{text-align:left;font-weight:700;}
tbody tr{cursor:pointer;}
tbody tr:hover td{background:#f0f6ff;}
.note{font-size:12.5px;color:var(--muted);margin:14px 0 0;}
.note a{color:var(--ink);font-weight:600;}
</style>
</head>
<body>
<nav class="navbar">
  <a href="index.html">Home</a>
  <a href="afl.html" class="current">AFL</a>
</nav>
<div class="page">

<div class="hero">
  <div class="eyebrow">AFL Player</div>
  <h1>${escapeHtml(label)}</h1>
  <p>${stats.games} games &middot; ${stats.firstSeason}&ndash;${stats.lastSeason} &middot; ${escapeHtml(stats.teams.join(", "))}</p>
</div>

<div id="summary">
  <div class="section-title">Career Summary</div>
  <div class="stats">
    <div class="stat-box"><strong>${stats.games}</strong><span>Games</span></div>
    <div class="stat-box"><strong>${stats.totalD}</strong><span>Total Disposals</span></div>
    <div class="stat-box"><strong>${stats.avgD}</strong><span>Avg Disposals</span></div>
    <div class="stat-box"><strong>${stats.totalG}</strong><span>Total Goals</span></div>
    <div class="stat-box"><strong>${stats.avgG}</strong><span>Avg Goals</span></div>
    <div class="stat-box"><strong>${stats.totalBR}</strong><span>Brownlow Votes</span></div>
  </div>
</div>

<div class="table-wrap">
<table>
<thead><tr><th>Season</th><th>Round</th><th>Team</th><th>Opponent</th><th>D</th><th>G</th><th>B</th><th>BR</th></tr></thead>
<tbody>${renderGameRows(dedup)}</tbody>
</table>
</div>

<p class="note">Search opponent splits, top-8 breakdowns and teammate comparisons on the <a href="afl-player.html?name=${encodeURIComponent(label.split(" (")[0])}">interactive player page</a>.</p>

</div>
</body>
</html>`;
}

// ---- Run ----
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

let built = 0;
const usedSlugs = new Set();

Object.entries(byPlayer).forEach(([name, games]) => {
  const identities = splitIntoIdentities(name, games);
  identities.forEach(identity => {
    const baseSlug = slugify(name) + (identity.slugSuffix || "");
    let slug = baseSlug;
    let i = 2;
    while (usedSlugs.has(slug)) { slug = `${baseSlug}-${i++}`; } // safety net for rare collisions
    usedSlugs.add(slug);

    const html = buildPage(identity.label, slug, identity.games);
    fs.writeFileSync(path.join(OUTPUT_DIR, `afl-player-${slug}.html`), html);
    built++;
  });
});

console.log(`\nDone. ${built} player pages built in ${OUTPUT_DIR}/`);
