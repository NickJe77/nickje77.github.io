let allData = [];
let filteredData = [];
let currentSort = { key: null, asc: true };

const yearFilter = document.getElementById("yearFilter");
const countryFilter = document.getElementById("countryFilter");
const raceSearch = document.getElementById("raceSearch");
const tableBody = document.querySelector("#g1-table tbody");
const headers = document.querySelectorAll("#g1-table thead th");

/* =========================
   Load data
   ========================= */
fetch("g1-results.json")
  .then(res => res.json())
  .then(data => {
    // Normalise empty country values
    allData = data.map(d => ({
      ...d,
      country: d.country && d.country.trim() !== "" ? d.country : "Unknown"
    }));

    populateFilters();
    applyFilters();
  })
  .catch(err => console.error("JSON load error:", err));

/* =========================
   Populate filters
   ========================= */
function populateFilters() {
  yearFilter.innerHTML = '<option value="">All</option>';
  countryFilter.innerHTML = '<option value="">All</option>';

  const years = [...new Set(allData.map(d => d.year))].sort((a, b) => b - a);
  const countries = [...new Set(allData.map(d => d.country))].sort();

  years.forEach(year => {
    const opt = document.createElement("option");
    opt.value = year;
    opt.textContent = year;
    yearFilter.appendChild(opt);
  });

  countries.forEach(country => {
    const opt = document.createElement("option");
    opt.value = country;
    opt.textContent = country;
    countryFilter.appendChild(opt);
  });
}

/* =========================
   Apply filters
   ========================= */
function applyFilters() {
  const yearVal = yearFilter.value;
  const countryVal = countryFilter.value;
  const raceVal = raceSearch.value.toLowerCase();

  filteredData = allData.filter(d => {
    return (
      (!yearVal || d.year == yearVal) &&
      (!countryVal || d.country === countryVal) &&
      (!raceVal || d.race.toLowerCase().includes(raceVal))
    );
  });

  renderTable(filteredData);
}

/* =========================
   Render table
   ========================= */
function renderTable(data) {
  tableBody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${row.year}</td>
      <td>${row.race}</td>
      <td>${row.track}</td>
      <td>${row.winner}</td>
      <td>${row.jockey}</td>
      <td>${row.trainer}</td>
      <td>${row.country}</td>
    `;

    tableBody.appendChild(tr);
  });
}

/* =========================
   Sorting
   ========================= */
headers.forEach(th => {
  th.addEventListener("click", () => {
    const key = th.dataset.key;
    if (!key) return;

    currentSort.asc = currentSort.key === key ? !currentSort.asc : true;
    currentSort.key = key;

    filtered
