document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#resultsTable tbody");
  const yearFilter = document.getElementById("yearFilter");
  const countryFilter = document.getElementById("countryFilter");
  const searchInput = document.getElementById("searchInput");

  let allData = [];

  fetch("data/g1-results.json")
    .then(res => {
      if (!res.ok) {
        throw new Error("Failed to load JSON");
      }
      return res.json();
    })
    .then(data => {
      allData = data;
      populateFilters(data);
      renderTable(data);
    })
    .catch(err => {
      console.error("DATA LOAD ERROR:", err);
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
    const search = searchInput.value.toLowerCase();

    const filtered = allData.filter(r => {
      return (
        (!year || r.year == year) &&
        (!country || r.country === country) &&
        (!search || r.race.toLowerCase().includes(search))
      );
    });

    renderTable(filtered);
  }

  yearFilter.addEventListener("change", applyFilters);
  countryFilter.addEventListener("change", applyFilters);
  searchInput.addEventListener("input", applyFilters);
});
