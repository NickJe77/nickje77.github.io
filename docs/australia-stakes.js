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

function renderTable(rows){
  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";

  rows.forEach(r=>{
    const year = r.date ? r.date.substring(0,4) : "";

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

/* -------- YEAR FILTER -------- */

function buildYearFilter(data){
  const years = new Set();
  data.forEach(r=>{
    if(r.date) years.add(r.date.substring(0,4));
  });

  const sel = document.getElementById("yearFilter");
  [...years].sort().reverse().forEach(y=>{
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    sel.appendChild(opt);
  });
}

/* -------- PREDICTIVE LISTS -------- */

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
  [...set].sort().forEach(v=>{
    const opt = document.createElement("option");
    opt.value = v;
    dl.appendChild(opt);
  });
}

/* -------- APPLY FILTERS -------- */

function applyFilters(){

  const year = yearFilter.value;
  const race = raceSearch.value.toLowerCase();
  const trainer = trainerSearch.value.toLowerCase();
  const jockey = jockeySearch.value.toLowerCase();

  const filtered = allRows.filter(r=>{
    const y = !year || (r.date && r.date.startsWith(year));
    const rMatch = !race || (r.grade && r.grade.toLowerCase().includes(race));
    const tMatch = !trainer || (r.trainer && r.trainer.toLowerCase().includes(trainer));
    const jMatch = !jockey || (r.jockey && r.jockey.toLowerCase().includes(jockey));
    return y && rMatch && tMatch && jMatch;
  });

  renderTable(filtered);
}
