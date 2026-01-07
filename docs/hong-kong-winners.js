/* =========================================================
   HONG KONG INTERNATIONAL RACES – WINNERS
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");

  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");
  const tableBody = document.querySelector(".archive-table tbody");

  let results = [];

  /* ---------- LOAD DATA ---------- */

  fetch("../data/hong-kong-results.json")
    .then(res => {
      if (!res.ok) {
        throw new Error("Failed to load hong-kong-results.json");
      }
      return res.json();
    })
    .then(data => {
      results = data;

      // Sort newest → oldest
      results.sort((a, b) => b.year - a.year);

      buildFilters(results);
      renderTable(results);
    })
    .catch(err => {
      console.error("Hong Kong Winners load error:", err);
      tableBody.innerHTML =
        `<tr><td colspan="5">Unable to load results.</td></tr>`;
    });

  /* ---------- BUILD FILTER OPTIONS ---------- */

  function buildFilters(data) {
    const years = [...new Set(data.map(r => r.year))].sort((a, b) => b - a);
    const races = [...new Set(data.map(r => r.race))].sort();
    const winners = [...new Set(data.map(r => r.winner))].sort();

    // Year dropdown
    years.forEach(year => {
      const opt = document.createElement("option");
      opt.value = year;
      opt.textContent = year;
      yearFilter.appendChild(opt);
    });

    // Race datalist
    races.forEach(race => {
      const opt = document.createElement("option");
      opt.value = race;
      raceList.appendChild(opt);
    });

    // Winner datalist
    winners.forEach(winner => {
      const opt = document.createElement("option");
      opt.value = winner;
      winnerList.appendChild(opt);
    });
  }

  /* ---------- APPLY FILTERS ---------- */

  function applyFilters() {
    const yearVal = yearFilter.value;
    const raceVal = raceFilter.value.toLowerCase();
    const winnerVal = winnerFilter.value.toLowerCase();

    const filtered = results.filter(r => {
      return (
        (yearVal === "" || r.year == yearVal) &&
        (raceVal === "" || r.race.toLowerCase().includes(raceVal)) &&
        (winnerVal === "" || r.winner.toLowerCase().includes(winnerVal))
      );
    });

    renderTable(filtered);
  }

  yearFilter.addEventListener("change", applyFilters);
  raceFilter.addEventListener("input", applyFilters);
  winnerFilter.addEventListener("input", applyFilters);

  /* ---------- RENDER TABLE ---------- */

  function renderTable(data) {
    tableBody.innerHTML = "";

    if (data.length === 0) {
      tableBody.innerHTML =
        `<tr><td colspan="5">No results found.</td></tr>`;
      return;
    }

    data.forEach(row => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${row.year}</td>
        <td>${row.race}</td>
        <td>${row.winner}</td>
        <td>${row.trainer}</td>
        <td>${row.jockey}</td>
      `;

      tableBody.appendChild(tr);
    });
  }
});
