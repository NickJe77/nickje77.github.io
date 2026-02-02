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

/* ---- COUNTRY NAME → ISO CODE MAP (core set) ---- */
const countryNameToISO = {
  "ENGLAND": "GB",
  "UNITED KINGDOM": "GB",
  "UK": "GB",
  "IRELAND": "IE",
  "FRANCE": "FR",
  "GERMANY": "DE",
  "ITALY": "IT",
  "SPAIN": "ES",
  "USA": "US",
  "UNITED STATES": "US",
  "AUSTRALIA": "AU",
  "JAPAN": "JP",
  "HONG KONG": "HK",
  "NEW ZEALAND": "NZ",
  "SOUTH AFRICA": "ZA",
  "CANADA": "CA",
  "BRAZIL": "BR",
  "ARGENTINA": "AR",
  "CHILE": "CL",
  "PERU": "PE",
  "URUGUAY": "UY",
  "MEXICO": "MX",
  "NETHERLANDS": "NL",
  "BELGIUM": "BE",
  "SWITZERLAND": "CH",
  "SWEDEN": "SE",
  "NORWAY": "NO",
  "DENMARK": "DK",
  "POLAND": "PL",
  "CZECH REPUBLIC": "CZ",
  "SLOVAKIA": "SK",
  "HUNGARY": "HU",
  "TURKEY": "TR",
  "GREECE": "GR",
  "RUSSIA": "RU",
  "CHINA": "CN",
  "SOUTH KOREA": "KR",
  "INDIA": "IN",
  "PAKISTAN": "PK",
  "SINGAPORE": "SG",
  "THAILAND": "TH",
  "MALAYSIA": "MY",
  "PHILIPPINES": "PH",
  "INDONESIA": "ID"
};

/* ---- ISO CODE → FLAG EMOJI ---- */
function isoToFlag(iso) {
  return iso
    ? String.fromCodePoint(...[...iso.toUpperCase()].map(c => 127397 + c.charCodeAt()))
    : "";
}

function countryToFlag(name) {
  if (!name) return "";
  const key = name.trim().toUpperCase();
  const iso = countryNameToISO[key];
  return iso ? isoToFlag(iso) : "";
}

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
    const flag = countryToFlag(row.COUNTRY);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.YEAR || ""}</td>
      <td>${row.RACE || ""}</td>
      <td>${row.TRACK || ""}</td>
      <td>${row.WINNER || ""}</td>
      <td>${row.TRAINER || ""}</td>
      <td>${row.JOCKEY || ""}</td>
      <td class="flag" title="${row.COUNTRY || ""}">${flag}</td>
    `;
    tableBody.appendChild(tr);
  });
}
