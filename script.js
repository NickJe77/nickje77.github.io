document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#results-table tbody");
  const yearFilter = document.getElementById("yearFilter");
  const searchInput = document.getElementById("searchInput");

  let allData = [];

  // ✅ FETCH DATA (RELATIVE PATH — CRITICAL)
  fetch("./data/g1-racing.json")
    .then(response => {
      if (!response.ok) {
        throw new Error("Failed to load racing data");
      }
      return response.json();
    })
    .then(data => {
      allData = data;
      populateYearFilter(data);
      renderTable(data);
    })
    .catch(error => {
      console.error("Racing data error:", error);
    });

  // =========================
  // Populate Year Dropdown
  // =========================
  function populateYearFilter(data) {
    const years = [...new Set(data.map(item => item.year))].sort((a, b) => b - a);

    years.forEach(year => {
      const option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      yearFilter.appendChild(option);
    });
  }

  // =========================
  // Render Table
  // =========================
  function renderTable(data) {
    tableBody.innerHTML = "";

    if (data.length === 0) {
      const row = document.createElement("tr");
      row.innerHTML = `<td colspan="7" style="text-align:center;">No results found</td>`;
      tableBody.appendChild(row);
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
        <td>${item.jockey}</td>
        <td>${item.trainer}</td>
      `;

      tableBody.appendChild(row);
    });
  }

  // =========================
  // Filters
  // =========================
  function applyFilters() {
    const selectedYear = yearFilter.value;
    const searchText = searchInput.value.toLowerCase();

    let filtered = allData;

    if (selectedYear !== "all") {
      filtered = filtered.filter(item => item.year.toString() === selectedYear);
    }

    if (searchText) {
      filtered = filtered.filter(item =>
        item.race.toLowerCase().includes(searchText)
      );
    }

    renderTable(filtered);
  }

  yearFilter.addEventListener("change", applyFilters);
  searchInput.addEventListener("input", applyFilters);
});
