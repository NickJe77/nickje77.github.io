// generate-afl-season-pages.js
//
// Reads docs/data/afl/afl_<year>.json for every season and outputs a
// genuine static HTML page per season: afl-<year>-season.html
// Run from inside your repo, e.g.:  node generate-afl-season-pages.js
//
// Requires nothing but Node's built-in fs module.

const fs = require("fs");
const path = require("path");

const START_YEAR = 1965;
const END_YEAR = 2026;
const DATA_DIR = path.join(__dirname, "data", "afl");
const OUTPUT_DIR = path.join(__dirname, "out"); // change to "." to write into repo root

// ---- Same lookup tables as the live page, so results match exactly ----
const TEAM_ALIASES = {
  "Brisbane": "Brisbane Lions",
  "GWS": "GWS GIANTS",
  "Greater Western Sydney": "GWS GIANTS",
  "Footscray": "Western Bulldogs",
  "West Coast": "West Coast Eagles",
  "Gold Coast": "Gold Coast SUNS",
  "Sydney": "Sydney Swans",
  "Kangaroos": "North Melbourne",
  "Fitzroy": "Fitzroy",
  "University": "University",
};
function normaliseTeam(name) {
  return TEAM_ALIASES[(name || "").trim()] ?? (name || "").trim();
}

const teamColours = {
  "Adelaide Crows": "#002B5C", "Brisbane Lions": "#7A1739", "Carlton": "#041E42",
  "Collingwood": "#1A1A1A", "Essendon": "#CC2031", "Fremantle": "#582C83",
  "Geelong": "#14498C", "Gold Coast SUNS": "#F7941D", "GWS GIANTS": "#F26522",
  "Hawthorn": "#7A4B23", "Melbourne": "#0F1E63", "North Melbourne": "#2C63B7",
  "Port Adelaide": "#008E97", "Richmond": "#FFD200", "St Kilda": "#8B0000",
  "Sydney Swans": "#EF3340", "West Coast Eagles": "#003C71",
  "Western Bulldogs": "#C8102E", "Fitzroy": "#7A1739",
};
function teamColour(name) { return teamColours[normaliseTeam(name)] || "#5a6472"; }

const finalsRounds = ["Elimination Final", "Qualifying Final", "Semi Final", "Preliminary Final", "Grand Final"];

function canonicalRound(r) {
  const t = (r ?? "").toLowerCase();
  if (t.includes("elimination")) return "Elimination Final";
  if (t.includes("qualifying")) return "Qualifying Final";
  if (t.includes("semi")) return "Semi Final";
  if (t.includes("preliminary")) return "Preliminary Final";
  if (t.includes("grand")) return "Grand Final";
  return (r ?? "").trim();
}
function roundNum(r) {
  const m = (r ?? "").match(/\d+/);
  return m ? +m[0] : Infinity;
}

// ---- Same match-building logic as the live page ----
function buildMatchesFromPlayers(rawData) {
  const map = {};
  rawData.forEach(p => {
    const home = normaliseTeam(p.home_team);
    const away = normaliseTeam(p.away_team);
    const key = `${canonicalRound(p.round)}|${home}|${away}`;
    if (!map[key]) {
      map[key] = {
        round: canonicalRound(p.round), home_team: home, away_team: away,
        home_points: p.home_points, away_points: p.away_points,
        players: [], date: p.date || "", venue: p.venue || "", crowd: p.crowd || "",
      };
    }
    map[key].players.push(p);
  });

  const gameMap = {};
  Object.values(map).forEach(m => {
    const teamKey = [m.home_team, m.away_team].sort().join("|");
    const gameKey = `${teamKey}|${m.home_points}|${m.away_points}`;
    if (!gameMap[gameKey] || roundNum(m.round) < roundNum(gameMap[gameKey].round)) {
      gameMap[gameKey] = m;
    }
  });
  return Object.values(gameMap);
}

function getStars(match) {
  return match.players
    .filter(p => +p.D >= 35 || +p.G >= 5)
    .sort((a, b) => (+b.G >= 5 ? +b.G * 6 : +b.D) - (+a.G >= 5 ? +a.G * 6 : +a.D))
    .slice(0, 3)
    .map(p => `<a href="afl-player.html?name=${encodeURIComponent(p.player)}">${escapeHtml(p.player)}</a> (${+p.G >= 5 ? `${p.G} goals` : `${p.D} disposals`})`);
}

function buildLadder(rows) {
  let ladder = {};
  rows.forEach(g => {
    const h = g.home_team, a = g.away_team, hp = +g.home_points, ap = +g.away_points;
    if (!ladder[h]) ladder[h] = { team: h, w: 0, l: 0, d: 0, f: 0, ag: 0 };
    if (!ladder[a]) ladder[a] = { team: a, w: 0, l: 0, d: 0, f: 0, ag: 0 };
    ladder[h].f += hp; ladder[h].ag += ap;
    ladder[a].f += ap; ladder[a].ag += hp;
    if (hp > ap) { ladder[h].w++; ladder[a].l++; }
    else if (ap > hp) { ladder[a].w++; ladder[h].l++; }
    else { ladder[h].d++; ladder[a].d++; }
  });
  return Object.values(ladder)
    .map(t => { t.p = t.ag ? ((t.f / t.ag) * 100).toFixed(1) : "0.0"; return t; })
    .sort((a, b) => (b.w - a.w) || ((b.d - a.d) * 0.5) || (b.p - a.p));
}

function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function swatch(team) {
  return `<span class="swatch" style="background:${teamColour(team)}"></span>`;
}

function gameLink(year, g) {
  return `afl-game.html?year=${year}&home=${encodeURIComponent(g.home_team)}&away=${encodeURIComponent(g.away_team)}&round=${encodeURIComponent(g.round)}`;
}

function renderMatchesHtml(year, matches) {
  return matches.map(g => {
    const line = g.home_points > g.away_points
      ? `${swatch(g.home_team)}${escapeHtml(g.home_team)} ${g.home_points} def ${swatch(g.away_team)}${escapeHtml(g.away_team)} ${g.away_points}`
      : g.home_points < g.away_points
      ? `${swatch(g.home_team)}${escapeHtml(g.home_team)} ${g.home_points} def by ${swatch(g.away_team)}${escapeHtml(g.away_team)} ${g.away_points}`
      : `${swatch(g.home_team)}${escapeHtml(g.home_team)} ${g.home_points} drew ${swatch(g.away_team)}${escapeHtml(g.away_team)} ${g.away_points}`;

    const stars = getStars(g);
    const winnerColour = g.home_points === g.away_points ? "transparent"
      : teamColour(g.home_points > g.away_points ? g.home_team : g.away_team);

    return `
    <div class="match" style="border-left-color:${winnerColour}" onclick="location.href='${gameLink(year, g)}'">
      <div class="round-label">${escapeHtml(g.round)}</div>
      <div class="line1">${line}</div>
      <div class="meta">${[g.date, g.venue, g.crowd && `Crowd: ${g.crowd}`].filter(Boolean).map(escapeHtml).join(" &middot; ")}</div>
      ${stars.length ? `<div class="stars">&#11088; ${stars.join(", ")}</div>` : ""}
    </div>`;
  }).join("");
}

function renderLadderHtml(rows) {
  let html = "<table><thead><tr><th>#</th><th>Team</th><th>W</th><th>L</th><th>D</th><th>%</th></tr></thead><tbody>";
  rows.forEach((t, i) => {
    html += `<tr><td>${i + 1}</td><td class="team">${swatch(t.team)}${escapeHtml(t.team)}</td><td>${t.w}</td><td>${t.l}</td><td>${t.d}</td><td>${t.p}</td></tr>`;
  });
  html += "</tbody></table>";
  return html;
}

function yearNavHtml(currentYear) {
  // Simple prev/next + link back to the interactive hub page.
  const hasPrev = currentYear > START_YEAR;
  const hasNext = currentYear < END_YEAR;
  return `
  <div class="year-nav">
    ${hasPrev ? `<a href="afl-${currentYear - 1}-season.html">&larr; ${currentYear - 1}</a>` : ""}
    <a href="afl-year.html">All seasons (interactive)</a>
    ${hasNext ? `<a href="afl-${currentYear + 1}-season.html">${currentYear + 1} &rarr;</a>` : ""}
  </div>`;
}

function buildPage(year, rawData) {
  const matches = buildMatchesFromPlayers(rawData);
  const nonFinals = matches.filter(m => !finalsRounds.includes(m.round));
  const ladder = buildLadder(nonFinals);

  const title = `${year} AFL Season — Ladder, Results &amp; Scores | The Sporting Almanac`;
  const description = `Full ${year} AFL season results: every match, final ladder standings, scores and best-on-ground players. Historical AFL data from The Sporting Almanac.`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<script src="/js/analytics.js"></script>
<meta charset="UTF-8" />
<title>${title}</title>
<meta name="description" content="${escapeHtml(description)}">
<link rel="canonical" href="https://thesportingalmanac.com/afl-${year}-season.html">
<link rel="stylesheet" href="style.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root{
  --bg:#eceff3; --surface:#ffffff; --ink:#0f141a; --muted:#69727c; --faint:#9aa3ad;
  --line:#e3e8ee; --board:#0a0a0a; --board-2:#1a1a1a; --board-line:rgba(255,255,255,.10);
  --win:#ffffff; --lose:rgba(255,255,255,.42); --accent:#e0b94a; --accent-soft:rgba(224,185,74,.18);
  --display:'Oswald',system-ui,sans-serif; --body:'Inter',system-ui,sans-serif; --radius:16px;
}
*{box-sizing:border-box;}
body{margin:0;font-family:var(--body);background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;}
.navbar{display:flex;justify-content:center;gap:26px;padding:15px;background:#fff;border-bottom:1px solid var(--line);font-weight:600;font-size:14px;}
.navbar a{text-decoration:none;color:var(--ink);opacity:.7;transition:opacity .15s;}
.navbar a:hover{opacity:1;}
.navbar a.current{opacity:1;color:var(--accent);}
.page-wrap{max-width:1180px;margin:0 auto;padding:26px 20px 70px;}
h1{font-family:var(--display);font-weight:600;font-size:clamp(24px,4vw,34px);letter-spacing:.01em;text-transform:uppercase;margin:0;}
.hero{position:relative;background:linear-gradient(160deg,var(--board-2),var(--board));border-radius:var(--radius);overflow:hidden;color:#fff;box-shadow:0 18px 40px -18px rgba(10,16,24,.55);margin-bottom:26px;padding:22px 26px 26px;}
.hero .eyebrow{font-family:var(--body);font-size:11.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:8px;}
.hero h1{color:#fff;}
.year-nav{display:flex;gap:16px;align-items:center;margin-bottom:16px;font-size:13px;font-weight:600;}
.year-nav a{color:var(--ink);text-decoration:none;background:#fff;border:1px solid var(--line);padding:8px 14px;border-radius:999px;}
.year-nav a:hover{border-color:var(--faint);}
.main-layout{display:grid;grid-template-columns:380px 1fr;gap:20px;align-items:start;}
@media(max-width:900px){ .main-layout{grid-template-columns:1fr;} }
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;}
.card-head{display:flex;align-items:center;padding:15px 18px;border-bottom:1px solid var(--line);}
.card-head h2{margin:0;font-family:var(--display);font-weight:600;font-size:15px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);}
.table-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;font-size:13px;}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap;}
thead th{background:#f7f9fb;font-family:var(--body);font-weight:600;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);text-align:center;}
thead th:nth-child(2){text-align:left;}
td{text-align:center;font-variant-numeric:tabular-nums;color:#27313c;}
td.team{text-align:left;font-weight:700;color:var(--ink);white-space:nowrap;}
td.team .swatch{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:8px;vertical-align:middle;}
tbody tr:hover td{background:#f0f6ff;}
.matches{display:flex;flex-direction:column;gap:10px;}
.match{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:14px 18px;cursor:pointer;transition:box-shadow .15s,transform .15s,border-color .15s;border-left:4px solid transparent;}
.match:hover{transform:translateY(-2px);box-shadow:0 10px 24px -14px rgba(10,16,24,.18);border-color:var(--faint);}
.match .round-label{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:6px;}
.match .line1{font-family:var(--display);font-weight:600;font-size:15.5px;letter-spacing:.01em;color:var(--ink);display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
.match .line1 .swatch{display:inline-block;width:9px;height:9px;border-radius:3px;flex:0 0 auto;}
.match .meta{color:var(--muted);font-size:12px;margin-top:6px;font-weight:600;letter-spacing:.02em;}
.match .stars{color:var(--muted);font-size:12px;margin-top:4px;}
.match .stars a{color:var(--ink);text-decoration:none;font-weight:600;}
.match .stars a:hover{color:var(--accent);text-decoration:underline;}
</style>
</head>
<body>
<nav class="navbar">
  <a href="index.html">Home</a>
  <a href="racing.html">Racing</a>
  <a href="afl.html" class="current">AFL</a>
  <a href="football.html">Football</a>
  <a href="cricket.html">Cricket</a>
  <a href="f1.html">F1</a>
</nav>

<div class="page-wrap">

<div class="hero">
  <div class="eyebrow">AFL</div>
  <h1>${year} AFL Season</h1>
</div>

${yearNavHtml(year)}

<div class="main-layout">
  <div class="card">
    <div class="card-head"><h2>Final Ladder</h2></div>
    <div class="table-wrap">${renderLadderHtml(ladder)}</div>
  </div>
  <div class="matches">${renderMatchesHtml(year, matches)}</div>
</div>

</div>
</body>
</html>`;
}

// ---- Run ----
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

let built = 0, skipped = 0;
for (let year = START_YEAR; year <= END_YEAR; year++) {
  const file = path.join(DATA_DIR, `afl_${year}.json`);
  if (!fs.existsSync(file)) { skipped++; continue; }
  const rawData = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!Array.isArray(rawData) || rawData.length === 0) { skipped++; continue; }
  const html = buildPage(year, rawData);
  fs.writeFileSync(path.join(OUTPUT_DIR, `afl-${year}-season.html`), html);
  built++;
  console.log(`Built afl-${year}-season.html (${rawData.length} rows)`);
}
console.log(`\nDone. ${built} pages built, ${skipped} years skipped (no data file found).`);
