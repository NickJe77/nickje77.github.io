const DATA_URL = "/data/vic-g1.json";

const RACE_MATCHES = [
  "W.S. COX PLATE",
  "WS COX PLATE",
  "COX PLATE"
];

let allRows = [];
let raceRows = [];

fetch(DATA_URL)
  .then(res => res.json())
  .then(data => {
    allRows = Array.isArray(data) ? data : [];

    raceRows = allRows.filter(r => isTargetRace(r.race));

    raceRows.sort((a,b) => b.year - a.year);

    buildYearFilter(raceRows);
    buildPredictiveLists(raceRows);
    renderTable(raceRows);
  })
  .catch(err => console.error("JSON load error:", err));

function isTargetRace(name){
  if(!name) return false;
  const n = name.toUpperCase();
  return RACE_MATCHES.some(x => n.includes(x));
}

function renderTable(rows){
  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";

  rows.forEach(r=>{
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.year || ""}</td>
      <td>${r.finish || ""}</td>
      <td>${r.horse || ""}</td>
      <td>${r.jockey || ""}</td>
      <td>${r.trainer || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* ---------- FILTERS ---------- */

function buildYearFilter(data){
  const years = new Set(data.map(r=>r.year).filter(Boolean));
  const sel = document.getElementById("yearFilter");
  sel.innerHTML = '<option value="">Year</option>';

  [...years].sort((a,b)=>b-a).forEach(y=>{
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    sel.appendChild(opt);
  });
}

function buildPredictiveLists(data){
  const horses = new Set();
  const trainers = new Set();
  const jockeys = new Set();

  data.forEach(r=>{
    if(r.horse) horses.add(r.horse);
    if(r.trainer) trainers.add(r.trainer);
    if(r.jockey) jockeys.add(r.jockey);
  });

  fillList("horseList", horses);
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
  const horseQ = horseSearch.value.toLowerCase();
  const trainerQ = trainerSearch.value.toLowerCase();
  const jockeyQ = jockeySearch.value.toLowerCase();

  const filtered = raceRows.filter(r=>{
    const yMatch = !year || String(r.year) === year;
    const hMatch = !horseQ || (r.horse && r.horse.toLowerCase().includes(horseQ));
    const tMatch = !trainerQ || (r.trainer && r.trainer.toLowerCase().includes(trainerQ));
    const jMatch = !jockeyQ || (r.jockey && r.jockey.toLowerCase().includes(jockeyQ));
    return yMatch && hMatch && tMatch && jMatch;
  });

  renderTable(filtered);
}
