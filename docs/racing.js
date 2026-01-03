let g1Data = [];
let currentSort = { key: null, dir: "asc" };

document.addEventListener("DOMContentLoaded", () => {
  fetch("g1-results.json")
    .then(res => res.json())
    .then(data => {
      g1Data = data;
      populateFilters(data);
      renderTable(data);
      enableSorting();
    })
    .catch(err => console.error("G1 LOAD ERROR:", err));

  document.getElementById("yearFilter").addEventListener("change", applyFilters);
  document.getElementById("countryFilter").addEventListener("change", applyFilters);
  document.getElementById("raceSearch").addEventListener("input", applyFilters);
});

function populateFilters(data) {
  const yearSet = new Set();
  const countrySet = new Set();

  data.forEach(row => {
    yearSet.add(row.year);
    countrySet.add(row.country);
  });

  const yearFilter = document.getElementById("yearFilter");
  [...yearSet].sort((a, b) => b - a).forEach(year => {
    yearFilter.innerHTML += `<option value="${year}">${year}</option>`;
  });

  const countryFilter = document.getElementById("countryFilter");
  [...countrySet].sort().forEach(country => {
    countryFilter.innerHTML += `<option value="${country}">${country}</option>`;
  });
}

function applyFilters() {
  const year = document.getElementById("yearFilter").value;
  const country = document.getElementById("countryFilter").value;
  const raceText = document.getElementById("raceSearch").value.toLowerCase();

  let filtered = g1Data;

  if (year) filtered = filtered.filter(r => r.year == year);
  if (country) filtered = filtered.filter(r => r.country === country);
  if (raceText) filtered = filtered.filter(r => r.race.toLowerCase().includes(raceText));

  if (currentSort.key) {
    filtered = sortData(filtered, currentSort.key, currentSort.dir);
  }

  renderTable(filtered);
}

function enableSorting() {
  document.querySelectorAll("#g1-table th").forEach(th => {
    th.style.cursor = "pointer";
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (!key) return;

      if (currentSort.key === key) {
        currentSort.dir = currentSort.dir === "asc" ? "desc" : "asc";
      } else {
        currentSort.key = key;
        currentSort.dir = "asc";
      }

      applyFilters();
    });
  });
}

function sortData(data, key, dir) {
  return [...data].sort((a, b) => {
    let valA = a[key];
    let valB = b[key];

    if (key === "year") {
      valA = Number(valA);
      valB = Number(valB);
    } else {
      valA = String(valA).toLowerCase();
      valB = String(valB).toLowerCase();
    }

    if (valA < valB) return dir === "asc" ? -1 : 1;
    if (valA > valB) return dir === "asc" ? 1 : -1;
    return 0;
  });
}

function renderTable(data) {
  const tbody = document.querySelector("#g1-table tbody");
  tbody.innerHTML = "";

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
    tbody.appendChild(tr);
  });
}
