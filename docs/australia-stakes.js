const yearFilter = document.getElementById("yearFilter");
const raceSearch = document.getElementById("raceSearch");
const trainerSearch = document.getElementById("trainerSearch");
const jockeySearch = document.getElementById("jockeySearch");

const raceList = document.getElementById("raceList");
const trainerList = document.getElementById("trainerList");
const jockeyList = document.getElementById("jockeyList");

const tableBody = document.getElementById("results-body");

let allData = [];

/* =========================
   CSV PARSER
========================= */
function parseCSV(text) {
  const lines = text.trim().split("\n");
  const headers = lines[0].split(",").map(h => h.trim());

  return lines.slice(1).map(line => {
    const values = line.split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/);
    let obj = {};
    headers.forEach((h, i) => {
      obj[h] = (values[i] || "").replace(/^"|"$/g, "").trim();
    });
    return obj;
  });
}

/* =========================
   LOAD CSV
========================= */
fetch("docs/data/racing/australia-stakes.csv")
  .then(res => res.text())
  .then(text => {
    allData = parseCSV(text);

    // add Year field extracted from Date
    allData.forEach(r => {
      if (r.Date) {
        r.Year = r.Date.split("/")[2]; // 1/1/1982 → 1982
      }
    });

    populateFilters(allData);
    renderTable(allData);
  })
  .catch(err => {
    console.error("CSV load failed:", err);
  });

/* =========================
   BUILD FILTERS
========================= */
function populateFilters(data) {
  const years = new Set();
  const races = new Set();
  const trainers = new Set();
  const jockeys = new Set();

  data.forEach(row => {
    if (row.Year) years.add(row.Year);
    if (row.Name) races.add(row.Name);
    if (row.Trainer) trainers.add(row.Trainer);
    if (row.Jockey) jockeys.add(row.Jockey);
  });

  [...years].sort((a,b)=>b-a).forEach(y => {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    yearFilter.appendChild(opt);
  });

  [...races].sort().forEach(r => {
    const opt = document.createElement("option");
    opt.value = r;
    raceList.appendChild(opt);
  });

  [...trainers].sort().forEach(t => {
    const opt = document.createElement("option");
    opt.value = t;
    trainerList.appendChild(opt);
  });

  [...jockeys].sort().forEach(j => {
    const opt = document.createElement("option");
    opt.value = j;
    jockeyList.appendChild(opt);
  });
}

/* =========================
   FILTER LOGIC
========================= */
function applyFilters() {
  const yearVal = yearFilter.value;
  const raceVal = raceSearch.value.toLowerCase();
  const trainerVal = trainerSearch.value.toLowerCase();
  const jockeyVal = jockeySearch.value.toLowerCase();

  const filtered = allData.filter(row => {
    return (
      (!yearVal || row.Year === yearVal) &&
      (!raceVal || row.Name.toLowerCase().includes(raceVal)) &&
      (!trainerVal || row.Trainer.toLowerCase().includes(trainerVal)) &&
      (!jockeyVal || row.Jockey.toLowerCase().includes(jockeyVal))
    );
  });

  renderTable(filtered);
}

/* =========================
   TABLE RENDER
========================= */
function renderTable(data) {
  tableBody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.Year || ""}</td>
      <td>${row.Name || ""}</td>
      <td>${row.Track || ""}</td>
      <td>${row.Winner || ""}</td>
      <td>${row.Trainer || ""}</td>
      <td>${row.Jockey || ""}</td>
    `;
    tableBody.appendChild(tr);
  });
}
