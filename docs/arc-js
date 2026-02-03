document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector("tbody");

  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");
  const jockeyFilter = document.getElementById("jockeyFilter");

  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");
  const jockeyList = document.getElementById("jockeyList");

  let allRows = [];

  console.log("Arc JS loaded");

  // arc.json MUST be in same folder as arc.html
  fetch("arc.json")
    .then(res => res.json())
    .then(data => {
      console.log("Rows loaded:", data.length);

      allRows = data.sort((a, b) => b.year - a.year);

      populateFilters(allRows);
      renderTable(allRows);
    })
    .catch(err => {
      console.error("Arc JSON load FAILED:", err);
    });

  function populateFilters(data) {
    const years = [...new Set(data.map(r => r.year))].sort((a,b)=>b-a);
    const races = [...new Set(data.map(r => r.race))].sort();
    const winners = [...new Set(data.map(r => r.winner))].sort();
    const jockeys = [...new Set(data.map(r => r.jockey))].sort();

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
      (!y || row.year == y) &&
      (!r || row.race.toLowerCase().includes(r)) &&
      (!w || row.winner.toLowerCase().includes(w)) &&
      (!j || row.jockey.toLowerCase().includes(j))
    );

    renderTable(filtered);
  }

  function renderTable(rows) {
    tbody.innerHTML = "";

    rows.forEach(r => {
      tbody.innerHTML += `
        <tr>
          <td>${r.year}</td>
          <td>${r.race}</td>
          <td>${r.winner}</td>
          <td>${r.trainer || ""}</td>
          <td>${r.jockey || ""}</td>
        </tr>
      `;
    });
  }

  yearFilter.addEventListener("change", applyFilters);
  raceFilter.addEventListener("input", applyFilters);
  winnerFilter.addEventListener("input", applyFilters);
  jockeyFilter.addEventListener("input", applyFilters);
});
