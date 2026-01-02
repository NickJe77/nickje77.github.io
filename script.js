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
      renderTable(data);
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
    const year = yearFilter.value;
    const country = countryFilter.value;
    const search = raceSearch.value.toLowerCase();

    let filtered = racingData;

    if (year) {
      filtered = filtered.filter(r => r.year == year);
    }

    if (country) {
      filtered = filtered.filter(r => r.country === country);
    }

    if (search) {
      filtered = filtered.filter(r =>
        r.race.toLowerCase().includes(search)
      );
    }

    renderTable(filtered);
  }

  yearFilter.addEventListener("change", applyFilters);
  countryFilter.addEventListener("change", applyFilters);
  raceSearch.addEventListener("input", applyFilters);
});
