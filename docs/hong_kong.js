document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector(".archive-table tbody");

  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");

  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");

  let allRows = [];

  fetch("hong-kong-results.json")
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      // Sort newest → oldest
      allRows = data.sort((a, b) => (b.year || 0) - (a.year || 0));
      populateFilters(allRows);
      renderTable(allRows);
    })
    .catch(err => {
      console.error("Hong Kong data load failed:", err);
    });

  function populateFilters(data) {
    const years = [...new Set(data.map(r => r.year).filter(Boolean))].sort((a, b) => b - a);
    const races = [...new Set(data.map(r => r.race).filter(Boolean))].sort();
    const winners = [...new Set(data.map(r => r.winner).filter(Boolean))].sort();

    years.forEach(y => {
      const opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      yearFilter.appendChild(opt);
    });

    races.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      raceList.appendChild(opt);
    });

    winners.forEach(w => {
      const opt = document.createElement("option");
      opt.value = w;
      winnerList.appendChild(opt);
    });
  }

  function applyFilters() {
    const yearVal = yearFilter.value;
    const raceVal = raceFilter.value.toLowerCase();
    const winnerVal = winnerFilter.value.toLowerCase();

    const filtered = allRows.filter(r =>
      (!yearVal || String(r.year) === yearVal) &&
      (!raceVal || String(r.race).toLowerCase().includes(raceVal)) &&
      (!winnerVal || String(r.winner).toLowerCase().includes(winnerVal))
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
});

