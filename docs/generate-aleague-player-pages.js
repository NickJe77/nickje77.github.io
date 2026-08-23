// generate-aleague-player-pages.js
//
// Reads docs/data/aleague/players.json (already aggregated by
// build_aleague_data.py) and writes one static HTML page per player:
// aleague-player-<slug>.html
//
// Run from inside docs/, e.g.:  node generate-aleague-player-pages.js

const fs = require("fs");
const path = require("path");

const PLAYERS_PATH = path.join(__dirname, "data", "aleague", "players.json");
const OUTPUT_DIR = path.join(__dirname, "out-aleague-players");

function escapeHtml(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function slugify(str) {
  return String(str).toLowerCase().replace(/'/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function renderSeasonRows(seasonStats) {
  return seasonStats.map(s => `
      <tr>
        <td>${escapeHtml(s.season)}</td>
        <td class="left">${escapeHtml(s.team)}</td>
        <td>${s.goals}</td>
        <td>${s.penalties}</td>
        <td>${s.own_goals}</td>
        <td>${s.yellow_cards}</td>
        <td>${s.red_cards}</td>
      </tr>`).join("");
}

function buildPage(player, slug) {
  const title = `${player.name} — A-League Career Stats | The Sporting Almanac`;
  const description = `${player.name}: A-League career record for ${player.teams.join(", ")} (${player.seasons[0]}–${player.seasons[player.seasons.length - 1]}). ${player.goals} goals, ${player.yellow_cards} yellow cards, ${player.red_cards} red cards.`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<script src="/js/analytics.js"></script>
<meta charset="UTF-8">
<title>${escapeHtml(title)}</title>
<meta name="description" content="${escapeHtml(description)}">
<link rel="canonical" href="https://thesportingalmanac.com/aleague-player-${slug}.html">
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
.page{max-width:900px;margin:0 auto;padding:26px 20px 70px;}
.hero{background:linear-gradient(160deg,var(--board-2),var(--board));border-radius:var(--radius);color:#fff;padding:22px 26px 26px;margin-bottom:20px;}
.eyebrow{font-size:11.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:8px;}
h1{margin:0;font-family:var(--display);font-weight:600;font-size:clamp(22px,4vw,34px);text-transform:uppercase;color:#fff;}
.hero p{margin:10px 0 0;color:rgba(255,255,255,.7);font-size:14px;}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin-bottom:20px;}
.section-title{margin:0 0 12px;font-family:var(--display);font-weight:600;color:var(--muted);text-transform:uppercase;font-size:12.5px;letter-spacing:.1em;}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;}
.stat-box{border:1px solid var(--line);border-radius:12px;padding:14px 10px;text-align:center;}
.stat-box strong{display:block;font-family:var(--display);font-weight:600;font-size:22px;}
.stat-box span{font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;}
.table-wrap{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);}
table{border-collapse:collapse;width:100%;font-size:13px;}
th,td{padding:9px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
th{background:#f7f9fb;font-weight:600;font-size:10.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);}
td.left{text-align:left;font-weight:700;}
</style>
</head>
<body>
<nav class="navbar">
  <a href="index.html">Home</a>
  <a href="aleague.html" class="current">A-League</a>
</nav>
<div class="page">
<div class="hero">
  <div class="eyebrow">A-League Player</div>
  <h1>${escapeHtml(player.name)}</h1>
  <p>${escapeHtml(player.teams.join(", "))} &middot; ${escapeHtml(player.seasons[0])}&ndash;${escapeHtml(player.seasons[player.seasons.length - 1])}</p>
</div>

<div class="card">
  <div class="section-title">Career Summary</div>
  <div class="stats">
    <div class="stat-box"><strong>${player.goals}</strong><span>Goals</span></div>
    <div class="stat-box"><strong>${player.penalties}</strong><span>Penalties</span></div>
    <div class="stat-box"><strong>${player.own_goals}</strong><span>Own Goals</span></div>
    <div class="stat-box"><strong>${player.yellow_cards}</strong><span>Yellow Cards</span></div>
    <div class="stat-box"><strong>${player.red_cards}</strong><span>Red Cards</span></div>
  </div>
</div>

<div class="table-wrap">
<table>
<thead><tr><th>Season</th><th>Team</th><th>Goals</th><th>Pens</th><th>OG</th><th>YC</th><th>RC</th></tr></thead>
<tbody>${renderSeasonRows(player.season_stats)}</tbody>
</table>
</div>

</div>
</body>
</html>`;
}

// ---- Run ----
fs.mkdirSync(OUTPUT_DIR, { recursive: true });
const players = JSON.parse(fs.readFileSync(PLAYERS_PATH, "utf8"));

let built = 0;
const usedSlugs = new Set();
players.forEach(player => {
  let slug = slugify(player.name);
  let i = 2;
  while (usedSlugs.has(slug)) { slug = `${slugify(player.name)}-${i++}`; }
  usedSlugs.add(slug);

  const html = buildPage(player, slug);
  fs.writeFileSync(path.join(OUTPUT_DIR, `aleague-player-${slug}.html`), html);
  built++;
});
console.log(`Done. ${built} player pages built.`);
