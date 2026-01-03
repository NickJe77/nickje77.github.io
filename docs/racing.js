document.addEventListener("DOMContentLoaded", () => {

  /* =========================
     State
     ========================= */
  let allData = [];
  let filteredData = [];
  let currentSort = { key: null, asc: true };

  /* =========================
     DOM refs (safe)
     ========================= */
  const tableBody = document.querySelector("#g1-table tbody");
  const headers = document.querySelectorAll("#g1-table thead th");

  const yearFilter = document.getElementById("yearFilter");
  const countryFilter = document.getElementById("countryFilter");
  const raceSearch = document.getElementById("raceSearch");

  if (!tableBody) {
    console.error("G1 table not found");
    return;
  }

  /* =========================
     Load JSON
     ========================= */
  fetch("g1-results.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON not found");
      return res.json();
    })
    .then(data => {
      if (!Array.isArray(data)) {
        data = data.results || data.data || [];
      }

      allData = data.map(row => ({
        year: row.year,
        race: row.race,
        track: row.track,
        winner: row.winner,
        jockey: row.jockey,
        trainer: row.trainer,
        country:
          row.country && row.country.trim() !== ""
            ? row.country
            : "Unknown"
      }));

      filteredData = [...allData];
      renderTable(filteredData);

      if (yearFilter && countryFilter) {
        populateFilters();
      }
    })
    .catch(err => {
      console.error("G1 load error:", err);
      tableBody.innerHTML =
        "<tr><td colspan='7'>No data available</td></tr>";
    });

  /* =========================
     Populate filters (optional)
     ========================= */
  function populateFilters() {
    yearFilter.innerHTML = '<option value="">All</option>';
    countryFilter.innerHTML = '<option value="">All</option>';

    const years = [...new Set(allData.map(d => d.year))]
      .sort((a, b) => b - a);

    const countries = [...new Set(allData.map(d => d.country))]
      .sort();

    years.forEach(year => {
      const o = document.createElement("option");
      o.value = year;
      o.textContent = year;
      yearFilter.appendChild(o);
    });

    countries.forEach(country => {
      const o = document.createElement("option");
      o.value = country;
      o.textContent = country;
      countryFilter.appendChild(o);
    });
  }

  /* =========================
     Apply filters
     ========================= */
  function applyFilters() {
    const yearVal = yearFilter?.value;
    const countryVal = countryFilter?.value;
    const raceVal = raceSearch?.value.toLowerCase() || "";

    filteredData = allData.filter(d =>
      (!yearVal || String(d.year) === yearVal) &&
      (!countryVal || d.country === countryVal) &&
      (!raceVal || d.race.toLowerCase().includes(raceVal))
    );

    renderTable(filteredData);
  }

  /* =========================
     Render table
     ========================= */
  function renderTable(data) {
    tableBody.innerHTML = "";

    if (!data.length) {
      tableBody.innerHTML =
        "<tr><td colspan='7'>No results found</td></tr>";
      return;
    }

    data.forEach(d => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${d.year}</td>
        <td>${d.race}</td>
        <td>${d.track}</td>
        <td>${d.winner}</td>
        <td>${d.jockey}</td>
        <td>${d.trainer}</td>
        <td>${d.country}</td>
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

      currentSort.asc =
        currentSort.key === key ? !currentSort.asc : true;
      currentSort.key = key;

      filteredData.sort((a, b) => {
        if (a[key] < b[key]) return currentSort.asc ? -1 : 1;
        if (a[key] > b[key]) return currentSort.asc ? 1 : -1;
        return 0;
      });

      renderTable(filteredData);
    });
  });

  /* =========================
     Events (only if filters exist)
     ========================= */
  yearFilter?.addEventListener("change", applyFilters);
  countryFilter?.addEventListener("change", applyFilters);
  raceSearch?.addEventListener("input", applyFilters);

});
