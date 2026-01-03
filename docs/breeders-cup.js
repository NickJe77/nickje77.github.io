document.addEventListener("DOMContentLoaded", () => {

  let allData = [];
  let filteredData = [];
  let currentSort = { key: null, asc: true };

  const tableBody = document.querySelector("#bc-table tbody");
  const headers = document.querySelectorAll("#bc-table thead th");
  const yearFilter = document.getElementById("yearFilter");
  const raceSearch = document.getElementById("raceSearch");

  if (!tableBody) return;

  /* =========================
     Load JSON
     ========================= */
  fetch("breeders-cup-results.json")
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
        trainer: row.trainer,
        jockey: row.jockey
      }));

      filteredData = [...allData];
      populateYearFilter();
      renderTable(filteredData);
    })
    .catch(() => {
      tableBody.innerHTML =
        "<tr><td colspan='6'>No data available</td></tr>";
    });

  /* =========================
     Populate year filter
     ========================= */
  function populateYearFilter() {
    yearFilter.innerHTML = '<option value="">All</option>';

    const years = [...new Set(allData.map(d => d.year))]
      .sort((a, b) => b - a);

    years.forEach(year => {
      const o = document.createElement("option");
      o.value = year;
      o.textContent = year;
      yearFilter.appendChild(o);
    });
  }

  /* =========================
     Apply filters
     ========================= */
  function applyFilters() {
    const yearVal = yearFilter.value;
    const raceVal = raceSearch.value.toLowerCase();

    filteredData = allData.filter(d =>
      (!yearVal || String(d.year) === yearVal) &&
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
        "<tr><td colspan='6'>No results found</td></tr>";
      return;
    }

    data.forEach(d => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${d.year}</td>
        <td>${d.race}</td>
        <td>${d.track}</td>
        <td>${d.winner}</td>
        <td>${d.trainer}</td>
        <td>${d.jockey}</td>
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
     Events
     ========================= */
  yearFilter.addEventListener("change", applyFilters);
  raceSearch.addEventListener("input", applyFilters);

});

