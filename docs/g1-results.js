// g1-results.js

const yearFilter = document.getElementById("yearFilter");
const raceFilter = document.getElementById("raceFilter");
const winnerFilter = document.getElementById("winnerFilter");
const jockeyFilter = document.getElementById("jockeyFilter");
const countryFilter = document.getElementById("countryFilter");

const raceList = document.getElementById("raceList");
const winnerList = document.getElementById("winnerList");
const jockeyList = document.getElementById("jockeyList");
const countryList = document.getElementById("countryList");

const tableBody = document.querySelector("tbody");
const resultCounter = document.getElementById("resultCounter");

let allData = [];

fetch("https://nickje77.github.io/docs/data/g1-results.json")
  .then(res => res.json())
  .then(data => {
    allData = data;
    populateFilters();
    applyFilters();
  });

function populateFilters() {
  const years = [...new Set(allData.map(d => d.YEAR))]
    .sort((a,b) => b - a);

  yearFilter.innerHTML = '<option value="">All</option>';
  years.forEach(y => {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    yearFilter.appendChild(opt);
  });

  fillDatalist(raceList, allData.map(d => d.RACE));
  fillDatalist(winnerList, allData.map(d => d.WINNER));
  fillDatalist(jockeyList, allData.map(d => d.JOCKEY));
  fillDatalist(countryList, allData.map(d => d.COUNTRY));
}

function fillDatalist(dl, arr) {
  const values = [...new Set(arr.filter(v => v && v !== ""))].sort();
  dl.innerHTML = "";
  values.forEach(v => {
    const opt = document.createElement("option");
    opt.value = v;
    dl.appendChild(opt);
  });
}

function applyFilters() {
  const y = yearFilter.value;
  const r = raceFilter.value.toLowerCase();
  const w = winnerFilter.value.toLowerCase();
  const j = jockeyFilter.value.toLowerCase();
  const c = countryFilter.value.toLowerCase();

  const filtered = allData.filter(row =>
    (!y || row.YEAR == y) &&
    (!r || row.RACE.toLowerCase().includes(r)) &&
    (!w || row.WINNER.toLowerCase().includes(w)) &&
    (!j || row.JOCKEY.toLowerCase().includes(j)) &&
    (!c || row.COUNTRY.toLowerCase().includes(c))
  );

  renderTable(filtered);

  resultCounter.textContent =
    "Showing " + filtered.length + " result" +
    (filtered.length !== 1 ? "s" : "");
}

function renderTable(rows) {
  tableBody.innerHTML = rows.map(row => `
    <tr>
      <td>${row.YEAR || ""}</td>
      <td>${row.RACE || ""}</td>
      <td>${row.TRACK || ""}</td>
      <td>${row.WINNER || ""}</td>
      <td>${row.TRAINER || ""}</td>
      <td>${row.JOCKEY || ""}</td>
      <td>${row.COUNTRY || ""}</td>
    </tr>
  `).join("");
}

[yearFilter, raceFilter, winnerFilter, jockeyFilter, countryFilter]
  .forEach(el => el.addEventListener("input", applyFilters));
