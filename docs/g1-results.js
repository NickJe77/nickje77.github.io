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

let allData = [];

// Country → flag map (use widely supported flags)
const countryFlags = {
  "ENGLAND": "🇬🇧",
  "IRELAND": "🇮🇪",
  "FRANCE": "🇫🇷",
  "GERMANY": "🇩🇪",
  "ITALY": "🇮🇹",
  "SPAIN": "🇪🇸",
  "USA": "🇺🇸",
  "UNITED STATES": "🇺🇸",
  "AUSTRALIA": "🇦🇺",
  "JAPAN": "🇯🇵",
  "HONG KONG": "🇭🇰",
  "NEW ZEALAND": "🇳🇿",
  "SOUTH AFRICA": "🇿🇦"
};

// LOAD DATA
fetch("../data/g1-results.json")
  .then(res => res.json())
  .then(data => {
    allData = data;
    populateFilters(data);
    renderTable(data);
  });

// BUILD FILTER OPTIONS
function populateFilters(data) {
  const years = new Set();
  const races = new Set();
  const winners = new Set();
  const jockeys = new Set();
  const countries = new Set();

  data.forEach(row => {
    if (row.YEAR) years.add(row.YEAR);
    if (row.RACE) races.add(row.RACE);
    if (row.WINNER) winners.add(row.WINNER);
    if (row.JOCKEY) jockeys.add(row.JOCKEY);
    if (row.COUNTRY) countries.add(row.COUNTRY);
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

  [...countries].sort().forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    countryList.appendChild(opt);
  });
}

// FILTER HANDLER
yearFilter.addEventListener("change", applyFilters);
raceFilter.addEventListener("input", applyFilters);
winnerFilter.addEventListener("input", applyFilters);
jockeyFilter.addEventListener("input", applyFilters);
countryFilter.addEventListener("input", applyFilters);

function applyFilters() {
  const yearVal = yearFilter.value;
  const raceVal = raceFilter.value.toLowerCase();
  const winnerVal = winnerFilter.value.toLowerCase();
  const jockeyVal = jockeyFilter.value.toLowerCase();
  const countryVal = countryFilter.value.toLowerCase();

  const filtered = allData.filter(row => {
    return (
      (!yearVal || row.YEAR == yearVal) &&
      (!raceVal || row.RACE.toLowerCase().includes(raceVal)) &&
      (!winnerVal || row.WINNER.toLowerCase().includes(winnerVal)) &&
      (!jockeyVal || row.JOCKEY.toLowerCase().includes(jockeyVal)) &&
      (!countryVal || row.COUNTRY.toLowerCase().includes(countryVal))
    );
  });

  renderTable(filtered);
}

// TABLE RENDER
function renderTable(data) {
  tableBody.innerHTML = "";

  data.forEach(row => {
    const countryKey = (row.COUNTRY || "").trim().toUpperCase();
    const flag = countryFlags[countryKey] || "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.YEAR || ""}</td>
      <td>${row.RACE || ""}</td>
      <td>${row.TRACK || ""}</td>
      <td>${row.WINNER || ""}</td>
      <td>${row.TRAINER || ""}</td>
      <td>${row.JOCKEY || ""}</td>
      <td class="flag" title="${countryKey}">${flag}</td>
    `;
    tableBody.appendChild(tr);
  });
}
