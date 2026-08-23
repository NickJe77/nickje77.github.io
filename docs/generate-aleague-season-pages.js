// generate-aleague-season-pages.js
//
// Reads docs/data/aleague/seasons/<season>.json (match list) and
// docs/data/aleague/team-stats.json (ladder) and writes one static
// HTML page per season: aleague-<season>-season.html
//
// Run from inside docs/, e.g.:  node generate-aleague-season-pages.js

const fs = require("fs");
const path = require("path");

const SEASONS_DIR = path.join(__dirname, "data", "aleague", "seasons");
const TEAM_STATS_PATH = path.join(__dirname, "data", "aleague", "team-stats.json");
const OUTPUT_DIR = path.join(__dirname, "out-aleague-seasons");

function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

const teamStats = JSON.parse(fs.readFileSync(TEAM_STATS_PATH, "utf8"));

function renderLadder(seasonId) {
  const rows = teamStats
    .filter(t => t.season === seasonId)
    // Finals/playoff rows currently leak into team-stats.json with round text
    // stuck onto the team name (e.g. "Perth GloryFinals Week 1,"). Those aren't
    // real ladder positions, so they're excluded here. Worth fixing at the
    // source in build_aleague_data.py when there's time.
    .filter(t => !/finals/i.test(t.team))
    .sort((a, b) => b.points - a.points || b.goal_difference - a.goal_difference || b.goals_for - a.goals_for);

  let html = "<table><thead><tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead><tbody>";
  rows.forEach((t, i) => {
    html += `<tr><td>${i + 1}</td><td class="left">${escapeHtml(t.team)}</td><td>${t.played}</td><td>${t.wins}</td><td>${t.draws}</td><td>${t.losses}</td><td>${t.goals_for}</td><td>${t.goals_against}</td><td>${t.goal_difference}</td><td><strong>${t.points}</strong></td></tr>`;
  });
  html += "</tbody></table>";
  return html;
}

function renderMatches(games) {
  return games.map(g => {
    const home = g.home || "TBC", away = g.away || "TBC";
    const hs = g.score_home, as = g.score_away;
    const known = hs !== undefined && hs !== null && as !== undefined && as !== null;
    const line = known
      ? `${escapeHtml(home)} ${hs} - ${as} ${escapeHtml(away)}`
      : `${escapeHtml(home)} vs ${escapeHtml(away)}`;
    return `
    <div class="match" onclick="location.href='aleague-match.html?season=${encodeURIComponent(g.season || "")}&matchId=${encodeURIComponent(g.match_id)}'">
      <div class="line1">${line}</div>
      ${g.date ? `<div class="meta">${escapeHtml(g.date)}</div>` : ""}
    </div>`;
  }).join("");
}

function buildPage(seasonId, data) {
  const games = (data.games || []).map(g => ({ ...g, season: seasonId }));
  const title = `${seasonId} A-League Season — Ladder, Results & Scores | The Sporting Almanac`;
  const description = `Full ${seasonId} A-League season: final ladder standings and every match result. Historical A-League data from The Sporting Almanac.`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<script src="/js/analytics.js"></script>
<meta charset="UTF-8">
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}">
<link rel="canonical" href="https://thesportingalmanac.com/aleague-${seasonId}-season.html">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#eceff3;--surface:#fff;--ink:#0f141a;--muted:#69727c;--line:#e3e8ee;--board:#0a1420;--board-2:#122236;--accent:#e0b94a;--display:'Oswald',system-ui,sans-serif;--body:'Inter',system-ui,sans-serif;--radius:16px;}
*{box-sizing:border-box;}
body{font-family:var(--body);margin:0;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;}
.navbar{display:flex;justify-content:center;gap:26px;padding:15px;background:#fff;border-bottom:1px solid var(--line);font-weight:600;font-size:14px;}
.navbar a{text-decoration:none;color:var(--ink);opacity:.7;}
.navbar a.current{opacity:1;color:var(--accent);}
.page{max-width:1180px;margin:0 auto;padding:26px 20px 70px;}
.hero{background:linear-gradient(160deg,var(--board-2),var(--board));border-radius:var(--radius);color:#fff;padding:22px 26px 26px;margin-bottom:20px;}
.eyebrow{font-size:11.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:8px;}
h1{margin:0;font-family:var(--display);font-weight:600;font-size:clamp(22px,4vw,34px);text-transform:uppercase;color:#fff;}
.main-layout{display:grid;grid-template-columns:420px 1fr;gap:20px;align-items:start;}
@media(max-width:900px){.main-layout{grid-template-columns:1fr;}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;}
.card-head{padding:15px 18px;border-bottom:1px solid var(--line);font-family:var(--display);font-weight:600;font-size:15px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);}
table{border-collapse:collapse;width:100%;font-size:13px;}
th,td{padding:8px 9px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
th{background:#f7f9fb;font-weight:600;font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);}
td.left{text-align:left;font-weight:700;}
.matches{display:flex;flex-direction:column;gap:8px;}
.match{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px;cursor:pointer;}
.match:hover{border-color:var(--accent);}
.match .line1{font-family:var(--display);font-weight:600;font-size:14.5px;}
.match .meta{color:var(--muted);font-size:11.5px;margin-top:4px;}
</style>
</head>
<body>
<nav class="navbar">
  <a href="index.html">Home</a>
  <a href="aleague.html" class="current">A-League</a>
</nav>
<div class="page">
<div class="hero">
  <div class="eyebrow">A-League</div>
  <h1>${escapeHtml(seasonId)} Season</h1>
</div>
<div class="main-layout">
  <div class="card">
    <div class="card-head">Final Ladder</div>
    ${renderLadder(seasonId)}
  </div>
  <div class="matches">${renderMatches(games)}</div>
</div>
</div>
</body>
</html>`;
}

// ---- Run ----
fs.mkdirSync(OUTPUT_DIR, { recursive: true });
const seasonFiles = fs.readdirSync(SEASONS_DIR).filter(f => f.endsWith(".json"));
let built = 0;
seasonFiles.forEach(f => {
  const seasonId = f.replace(".json", "");
  const data = JSON.parse(fs.readFileSync(path.join(SEASONS_DIR, f), "utf8"));
  const html = buildPage(seasonId, data);
  fs.writeFileSync(path.join(OUTPUT_DIR, `aleague-${seasonId}-season.html`), html);
  built++;
  console.log(`Built aleague-${seasonId}-season.html (${(data.games || []).length} games)`);
});
console.log(`\nDone. ${built} season pages built.`);
