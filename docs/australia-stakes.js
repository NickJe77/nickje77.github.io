const DATA_URL = "/data/australia-stakes.json";
let allRows = [];

fetch(DATA_URL)
  .then(res => res.json())
  .then(data => {
    allRows = data;
    buildYearFilter(data);
    buildPredictiveLists(data);
    renderTable(data);
  });

function extractYear(dateStr) {
  if (!dateStr) return "";
  const parts = dateStr.split("/");
  return parts.length === 3 ? parts[2] : "";
}

function renderTable(rows){
  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";

  rows.forEach(r=>{
    const year = extractYear(r.date);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${year}</td>
      <td>${r.grade || ""}</td>
      <td>${r.track || ""}</td>
      <td>${r.winner || ""}</td>
      <td>${r.trainer || ""}</td>
      <td>${r.jockey || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

function buildYearFilter(data){
  const years = new Set();

  data.forEach(r=>{
    const y = extractYear(r.date);
    if (y) years.add(y);
  });

  const sel = document.getElementById("yearFilter");
  [...years].sort().reverse().forEach(y=>{
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    sel.appendChild(opt);
  });
}

function buildPredictiveLists(data){
  const races = new Set();
  const trainers = new Set();
  const jockeys = new Set();

  data.forEach(r=>{
    if(r.grade) races.add(r.grade);
    if(r.trainer) trainers.add(r.trainer);
    if(r.jockey) jockeys.add(r.jockey);
  });

  fillList("raceList", races);
  fillList("trainerList", trainers);
  fillList("jockeyList", jockeys);
}

function fillList(id, set){
  const dl = document.getElementById(id);
  dl.innerHTML = "";
  [...set].sort().forEach(v=>{
    const opt = document.createElement("option");
    opt.value = v;
    dl.appendChild(opt);
  });
}

function applyFilters(){
  const year = yearFilter.value;
  const race = raceSearch.value.toLowerCase();
  const trainer = trainerSearch.value.toLowerCase();
  const jockey = jockeySearch.value.toLowerCase();

  const filtered = allRows.filter(r=>{
    const y = extractYear(r.date);

    const yMatch = !year || y === year;
    const rMatch = !race || (r.grade && r.grade.toLowerCase().includes(race));
    const tMatch = !trainer || (r.trainer && r.trainer.toLowerCase().includes(trainer));
    const jMatch = !jockey || (r.jockey && r.jockey.toLowerCase().includes(jockey));

    return yMatch && rMatch && tMatch && jMatch;
  });

  renderTable(filtered);
}
