const yearFilter = document.getElementById("yearFilter");
const raceFilter = document.getElementById("raceFilter");
const winnerFilter = document.getElementById("winnerFilter");
const jockeyFilter = document.getElementById("jockeyFilter");

const raceList = document.getElementById("raceList");
const winnerList = document.getElementById("winnerList");
const jockeyList = document.getElementById("jockeyList");

const tableBody = document.querySelector("tbody");
const statusBox = document.getElementById("statusBox");

let allData = [];

// ---- helpers ----
function setStatus(msg) {
  if (statusBox) statusBox.textContent = msg;
}

function describeUrl(url) {
  try {
    return new URL(url, window.location.href).href;
  } catch {
    return url;
  }
}

function unwrapToArray(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  if (data && Array.isArray(data.data)) return data.data;
  if (data && Array.isArray(data.rows)) return data.rows;
  if (data && Array.isArray(data.items)) return data.items;
  return null;
}

// ---- LOAD DATA ----
const DATA_URL = "../data/g1_results.json";
setStatus(`Loading JSON…\nURL: ${describeUrl(DATA_URL)}`);

fetch(DATA_URL, { cache: "no-store" })
  .then(async (res) => {
    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status} ${res.statusText}\nURL: ${describeUrl(DATA_URL)}\n\nBody (first 200 chars):\n${(txt || "").slice(0, 200)}`);
    }
    return res.json().catch(() => {
      throw new Error(`JSON parse error.\nURL: ${describeUrl(DATA_URL)}\n(That usually means the file is not valid JSON, or GitHub is serving HTML instead.)`);
    });
  })
  .then((data) => {
    const arr = unwrapToArray(data);
    if (!arr) {
      setStatus(
        `Loaded JSON, but it is NOT an array (or wrapped as results/data/rows/items).\n` +
        `URL: ${describeUrl(DATA_URL)}\n\n` +
        `Top-level keys: ${data && typeof data === "object" ? Object.keys(data).join(", ") : "n/a"}`
      );
      allData = [];
      renderTable(allData);
      return;
    }

    allData = arr;

    setStatus(
      `Loaded ✅\n` +
      `Rows: ${allData.length}\n` +
      `URL: ${describeUrl(DATA_URL)}`
    );

    populateFilters(allData);
    renderTable(allData);
  })
  .catch((err) => {
    setStatus(`FAILED ❌\n${err.message}`);
    allData = [];
    renderTable(allData);
  });

// ---- BUILD FILTER OPTIONS ----
function populateFilters(data) {
  // clear existing options to avoid duplicates if reloaded
  yearFilter.querySelectorAll("option:not([value=''])").forEach(o => o.remove());
  raceList.innerHTML = "";
  winnerList.innerHTML = "";
  jockeyList.innerHTML = "";

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

  [...years].sort((a, b) => b - a).forEach(y => {
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

// ---- FILTER HANDLER ----
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
    const race = (row.race || "").toLowerCase();
    const winner = (row.winner || "").toLowerCase();
    const jock = (row.jock || "").toLowerCase();

    return (
      (!yearVal || String(row.year) === String(yearVal)) &&
      (!raceVal || race.includes(raceVal)) &&
      (!winnerVal || winner.includes(winnerVal)) &&
      (!jockeyVal || jock.includes(jockeyVal))
    );
  });

  renderTable(filtered);
}

// ---- TABLE RENDER ----
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
