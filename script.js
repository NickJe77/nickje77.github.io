document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#racingTable tbody");
  if (!tableBody) return;

  const yearFilter = document.getElementById("yearFilter");
  const countryFilter = document.getElementById("countryFilter");
  const raceSearch = document.getElementById("raceSearch");

  let racingData = [];

  fetch("./data/g1-racing.json")
    .then(res => res.json())
    .then(data => {
      racingData = data;

      populateFilters(data);
      renderTable(data); // 🔑 ALWAYS render full table first
    });

  function populateFilters(data) {
    const years = [...new Set(data.map(r => r.year))].sort((a, b) => b - a);
    const countries = [...new Set(data.map(r => r.country))].sort();

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

  function renderTable(data) {
    tableBody.innerHTML = "";

    if (data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="opacity:0.6;">No races match your filters</td>
        </tr>
      `;
      return;
    }

    data.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.year}</td>
        <td>${row.race}</td>
        <td>${row.country}</td>
        <td>${row.track}</td>
        <td>${row.winner}</td>
        <td>${row.jockey}</td>
        <td>${row.trainer}</td>
      `;
      tableBody.appendChild(tr);
    });
  }

  function applyFilters() {
    let filtered = racingData;

    const year = yearFilter.valu
