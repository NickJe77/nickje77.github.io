<!DOCTYPE html>
<html lang="en">
<head>
  <script src="/js/analytics.js"></script>
  <meta charset="UTF-8">
  <title>Tennis | The Sporting Almanac</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body{
  font-family:Inter,system-ui,Arial;
  margin:0;
  background:#f4f6f8;
}

.navbar{
  display:flex;
  justify-content:center;
  gap:22px;
  padding:16px 0;
  background:#fff;
  border-bottom:1px solid #ddd;
}
.navbar a{
  color:#0056d6;
  text-decoration:none;
  font-weight:600;
}

.hero{
  background:linear-gradient(90deg,#2e7d32,#43a047);
  color:white;
  padding:40px;
  text-align:center;
}

.controls{
  max-width:1200px;
  margin:20px auto;
  display:flex;
  gap:12px;
}

select,input{
  flex:1;
  padding:12px;
  border-radius:10px;
  border:1px solid #ccc;
}

.grid{
  max-width:1200px;
  margin:0 auto;
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:20px;
  padding:20px;
}

.card{
  background:#fff;
  padding:20px;
  border-radius:16px;
  box-shadow:0 4px 10px rgba(0,0,0,0.05);
}

.surface{
  display:inline-block;
  margin-top:10px;
  padding:6px 12px;
  border-radius:20px;
  background:#e8f5e9;
  font-size:12px;
}

.empty{
  text-align:center;
  padding:40px;
  color:#777;
}
</style>
</head>

<body>

<div class="navbar">
  <a href="/">Home</a>
  <a href="/tennis.html">Tennis</a>
</div>

<div class="hero">
  <h1>Tennis</h1>
  <p>Full match database (ATP + WTA)</p>
</div>

<div class="controls">
  <select id="year">
    <option value="2026">2026</option>
    <option value="2025">2025</option>
    <option value="2024">2024</option>
  </select>

  <input id="search" placeholder="Search tournaments">
</div>

<div id="grid" class="grid"></div>

<script>
const grid = document.getElementById("grid");
const yearSelect = document.getElementById("year");
const searchInput = document.getElementById("search");

let data = [];

async function loadYear(year){

  grid.innerHTML = "<div class='empty'>Loading...</div>";

  try{
    const res = await fetch(`/docs/data/tennis/seasons/${year}.json`);
    const json = await res.json();

    data = json;
    render();

  }catch(e){
    grid.innerHTML = "<div class='empty'>Failed to load data</div>";
  }
}

function render(){

  const term = searchInput.value.toLowerCase();

  const filtered = data.filter(t =>
    t.tournament.toLowerCase().includes(term)
  );

  if(!filtered.length){
    grid.innerHTML = "<div class='empty'>No tournaments found for this year.</div>";
    return;
  }

  grid.innerHTML = filtered.map(t => `
    <div class="card">
      <h3>${t.tournament}</h3>
      <div class="surface">${t.surface || "Unknown"}</div>
    </div>
  `).join("");
}

yearSelect.addEventListener("change", () => loadYear(yearSelect.value));
searchInput.addEventListener("input", render);

// initial load
loadYear(yearSelect.value);
</script>

</body>
</html>
