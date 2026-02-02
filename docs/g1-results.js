const yearFilter = document.getElementById("yearFilter");
const raceFilter = document.getElementById("raceFilter");
const winnerFilter = document.getElementById("winnerFilter");
const jockeyFilter = document.getElementById("jockeyFilter");

const raceList = document.getElementById("raceList");
const winnerList = document.getElementById("winnerList");
const jockeyList = document.getElementById("jockeyList");

const tableBody = document.querySelector("tbody");

let allData = [];

// LOAD DATA (DO NOT CHANGE PATH)
fetch("../data/g1_results.json")
  .then(res => res.json())
  .then(data => {
    // SAFELY UNWRAP ARRAY
    if (Array.isArray(data)) {
      allData = data;
    } else if (Array.isArray(data.results)) {
      allData = data.results;
    } else if (Array.isArray(data.data)) {
      allData = data.data;
    } else {
      console.error("Unknown JSON structure:", data);
      allData = [];
    }

    populateFilters(allData);
    renderTable(allData);
  })
  .catch(err => console.error("Fetch error:", err));

// BUILD FILTER OPTIONS
function populateFilters(data) {
  const years = new Set();
  const races = new Set();
  const winners = new Set();
  const jockeys = new Set();

  data.forEach(row => {
    if (row.year) years.add(row.year);
    if (row.race) races.add(row.race);
    if (row.winner) winners.add(row.winner);
    if (row.jock) jockeys.add(row.jock);
  });

  [...years].sort((a,b)=>b-a).forEach(y => {
    const opt = document.createElement("option");
    opt.value = y;
    yearFilter.appendChild(opt);
  });

  [...races].sort().forEach(r => {
    const opt = document.createElement("option");
    opt.value = r;
    raceList.appendChild(opt);
  });

  [...winners].sort().forEach(w => {
    const opt = document.createElement("option");
    opt.value = w;
    winnerList.appendChild(opt);
  });

  [...jockeys].sort().forEach(j => {
    const opt = document.createElement("option");
    opt.value = j;
    jockeyList.appendChild(opt);
  });
}

// FILTER HANDLER
yearFilter.addEventListener("change", applyFilters);
raceFilter.addEventListener("input", applyFilters);
winnerFilter.addEventListener("input", applyFilters);
jockeyFilter.addEventListener("input", applyFilters);

function applyFilters() {
  const yearVal = yearFilter.value;
  const raceVal = raceFilter.value.toLowerCase();
  const winnerVal = winnerFilter.value.toLowerCase();
  const jockeyVal = jockeyFilter.value.toLowerCase();

  const filtered = allData.filter(row => {
    return (
      (!yearVal || row.year == yearVal) &&
      (!raceVal || row.race.toLowerCase().includes(raceVal)) &&
      (!winnerVal || row.winner.toLowerCase().includes(winnerVal)) &&
      (!jockeyVal || row.jock.toLowerCase().includes(jockeyVal))
    );
  });

  renderTable(filtered);
}

// TABLE RENDER
function renderTable(data) {
  tableBody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.year || ""}</td>
      <td>${row.race || ""}</td>
      <td>${row.track || ""}</td>
      <td>${row.winner || ""}</td>
      <td>${row.trainer || ""}</td>
      <td>${row.jock || ""}</td>
      <td>${row.country || ""}</td>
    `;
    tableBody.appendChild(tr);
  });
}
