document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#results-table tbody");
  const yearFilter = document.getElementById("yearFilter");
  const countryFilter = document.getElementById("countryFilter");
  const searchInput = document.getElementById("searchInput");

  let allData = [];

  fetch("./data/g1-racing.json")
    .then(res => res.json())
    .then(data => {
      // Normalise field names once
      allData = data.map(item => ({
        year: item.year,
        race: item.race,
        country: item.country || item.Country || item.COUNTRY,
        track: item.track,
        winner: item.winner,
        jockey: item.jockey,
        trainer: item.trainer
      }));

      populateYearFilter(allData);
      populateCountryFilter(allData);
      renderTable(allData);
    });

  function populateYearFilter(data) {
    const years = [...new Set(data.map(d => d.year))].sort((a, b) => b - a);
    years.forEach(year => {
      const opt = document.createElement("option");
      opt.value = year;
      opt.textContent = year;
      yearFilter.appendChild(opt);
    });
  }

  function populateCountryFilter(data) {
    const countries = [...new Set(data.map(d => d.country))]
      .filter(Boolean)
      .sort();

    countries.forEach(country => {
      const opt = document.createElement("option");
      opt.value = country;
      opt.textContent = country;
      countryFilter.appendChild(opt);
    });
  }

  function renderTable(data) {
    tableBody.innerHTML = "";

    if (!data.length) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; opacity:0.6;">
            No races match your filters
          </td>
        </tr>`;
      return;
    }

    data.forEach(item => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${item.year}</td>
        <td>${item.race}</td>
        <td>${item.country}</td>
        <td>${item.track}</td>
        <td>${item.winner}</td>
        <td>${item.jockey}</
