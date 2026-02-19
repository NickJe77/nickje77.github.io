document.addEventListener("DOMContentLoaded", function() {

  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");
  const jockeyFilter = document.getElementById("jockeyFilter");
  const trainerFilter = document.getElementById("trainerFilter"); // NEW
  const countryFilter = document.getElementById("countryFilter");
  const tableBody = document.getElementById("g1Body");
  const resultCounter = document.getElementById("resultCounter");

  let allData = [];

  fetch("data/g1-results.json")
    .then(res => res.json())
    .then(data => {
      allData = data;
      populateYears();
      applyFilters();
    })
    .catch(err => {
      console.error("JSON load error:", err);
    });

  function populateYears() {
    const years = [...new Set(allData.map(d => Number(d.YEAR)))]
      .sort((a,b) => b - a);

    yearFilter.innerHTML = '<option value="">All</option>';
    years.forEach(y => {
      if (!isNaN(y)) {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        yearFilter.appendChild(opt);
      }
    });
  }

  function applyFilters() {
    const y = yearFilter.value;
    const r = raceFilter.value.toLowerCase();
    const w = winnerFilter.value.toLowerCase();
    const j = jockeyFilter.value.toLowerCase();
    const t = trainerFilter ? trainerFilter.value.toLowerCase() : ""; // NEW
    const c = countryFilter.value.toLowerCase();

    const filtered = allData.filter(row =>
      (!y || row.YEAR == y) &&
      (!r || (row.RACE || "").toLowerCase().includes(r)) &&
      (!w || (row.WINNER || "").toLowerCase().includes(w)) &&
      (!j || (row.JOCKEY || "").toLowerCase().includes(j)) &&
      (!t || (row.TRAINER || "").toLowerCase().includes(t)) && // NEW
      (!c || (row.COUNTRY || "").toLowerCase().includes(c))
    );

    renderTable(filtered);

    resultCounter.textContent =
      "Showing " + filtered.length + " result" +
      (filtered.length !== 1 ? "s" : "");
  }

  function renderTable(rows) {
    tableBody.innerHTML = rows.map(row => `
      <tr>
        <td>${row.YEAR || ""}</td>
        <td>${row.RACE || ""}</td>
        <td>${row.TRACK || ""}</td>
        <td>${row.WINNER || ""}</td>
        <td>${row.TRAINER || ""}</td>
        <td>${row.JOCKEY || ""}</td>
        <td>${row.COUNTRY || ""}</td>
      </tr>
    `).join("");
  }

  // Attach listeners
  [yearFilter, raceFilter, winnerFilter, jockeyFilter, trainerFilter, countryFilter]
    .forEach(el => {
      if (el) el.addEventListener("input", applyFilters);
    });

});
