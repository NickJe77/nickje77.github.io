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

fetch("g1-results.json")
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

  populateDatalist(raceList, "RACE");
  populateDatalist(winnerList, "WINNER");
  populateDatalist(jockeyList, "JOCKEY");
  populateDatalist(countryList, "COUNTRY");
}

function populateDatalist(listElement, key) {
  const values = [...new Set(allData.map(d => d[key]))]
    .filter(Boolean)
    .sort();

  listElement.innerHTML = "";
  values.forEach(v => {
    const opt = document.createElement("option");
    opt.value = v;
    listElement.appendChild(opt);
  });
}

function applyFilters() {
  const yearVal = yearFilter.value;
  const raceVal = raceFilter.value.toLowerCase();
  const winnerVal = winnerFilter.value.toLowerCase();
  const jockeyVal = jockeyFilter.value.toLowerCase();
  const countryVal = countryFilter.value.toLowerCase();

  const filtered = allData.filter(row =>
    (!yearVal || row.YEAR == yearVal) &&
    (!raceVal || row.RACE.toLowerCase().includes(raceVal)) &&
    (!winnerVal || row.WINNER.toLowerCase().includes(winnerVal)) &&
    (!jockeyVal || row.JOCKEY.toLowerCase().includes(jockeyVal)) &&
    (!countryVal || row.COUNTRY.toLowerCase().includes(countryVal))
  );

  renderTable(filtered);
  resultCounter.textContent =
    "Showing " + filtered.length + " result" +
    (filtered.length !== 1 ? "s" : "");
}

function renderTable(data) {
  tableBody.innerHTML = data.map(row => `
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
