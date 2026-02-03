document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector(".archive-table tbody");

  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");
  const jockeyFilter = document.getElementById("jockeyFilter");

  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");
  const jockeyList = document.getElementById("jockeyList");

  let allRows = [];

  console.log("Dubai World Cup JS loaded");

  fetch("dubai-world-cup.json")
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      allRows = data.sort((a, b) => (b.year || 0) - (a.year || 0));
      populateFilters(allRows);
      renderTable(allRows);
    })
    .catch(err => {
      console.error("Dubai World Cup data load failed:", err);
    });

  function populateFilters(data) {
    const years = [...new Set(data.map(r => r.year).filter(Boolean))].sort((a, b) => b - a);
    const races = [...new Set(data.map(r => r.race).filter(Boolean))].sort();
    const winners = [...new Set(data.map(r => r.winner).filter(Boolean))].sort();
    const jockeys = [...new Set(data.map(r => r.jockey).filter(Boolean))].sort();

    years.forEach(y => yearFilter.innerHTML += `<option value="${y}">${y}</option>`);
    races.forEach(r => raceList.innerHTML += `<option value="${r}">`);
    winners.forEach(w => winnerList.innerHTML += `<option value="${w}">`);
    jockeys.forEach(j => jockeyList.innerHTML += `<option value="${j}">`);
  }

  function applyFilters() {
    const y = yearFilter.value;
    const r = raceFilter.value.toLowerCase();
    const w = winnerFilter.value.toLowerCase();
    const j = jockeyFilter.value.toLowerCase();

    const filtered = allRows.filter(row =>
      (!y || String(row.year) === y) &&
      (!r || String(row.race).toLowerCase().includes(r)) &&
      (!w || String(row.winner).toLowerCase().includes(w)) &&
      (!j || String(row.jockey).toLowerCase().includes(j))
    );

    renderTable(filtered);
  }

  function renderTable(rows) {
    tbody.innerHTML = "";

    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.year || ""}</td>
        <td>${r.race || ""}</td>
        <td>${r.winner || ""}</td>
        <td>${r.trainer || ""}</td>
        <td>${r.jockey || ""}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  yearFilter.addEventListener("change", applyFilters);
  raceFilter.addEventListener("input", applyFilters);
  winnerFilter.addEventListener("input", applyFilters);
  jockeyFilter.addEventListener("input", applyFilters);
});
