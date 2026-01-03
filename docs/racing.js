let g1Data = [];

document.addEventListener("DOMContentLoaded", () => {
  fetch("g1-results.json")
    .then(res => res.json())
    .then(data => {
      g1Data = data;
      populateFilters(data);
      renderTable(data);
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

  if (year) {
    filtered = filtered.filter(row => row.year == year);
  }

  if (country) {
    filtered = filtered.filter(row => row.country === country);
  }

  if (raceText) {
    filtered = filtered.filter(row =>
      row.race.toLowerCase().includes(raceText)
    );
  }

  renderTable(filtered);
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
