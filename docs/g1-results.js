document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector(".archive-table tbody");

  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");

  let allRows = [];

  if (!tbody) {
    console.error("Table body not found");
    return;
  }

  fetch("g1-results.json")
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      if (!Array.isArray(data)) {
        console.error("JSON is not an array");
        return;
      }

      allRows = data;

      populateFilters(data);
      renderTable(data);
    })
    .catch(err => {
      console.error("Failed to load results:", err);
    });

  function populateFilters(data) {
    const years = [...new Set(data.map(r => r.year).filter(Boolean))].sort();
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
      opt.textContent = r;
      raceFilter.appendChild(opt);
    });

    winners.forEach(w => {
      const opt = document.createElement("option");
      opt.value = w;
      opt.textContent = w;
      winnerFilter.appendChild(opt);
    });
  }

  function applyFilters() {
    const yearVal = yearFilter.value;
    const raceVal = raceFilter.value;
    const winnerVal = winnerFilter.value;

    const filtered = allRows.filter(r => {
      return (
        (!yearVal || r.year == yearVal) &&
        (!raceVal || r.race === raceVal) &&
        (!winnerVal || r.winner === winnerVal)
      );
    });

    renderTable(filtered);
  }

  function renderTable(rows) {
    tbody.innerHTML = "";

    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.year || ""}</td>
        <td>${r.race || ""}</td>
        <td>${r.track || ""}</td>
        <td>${r.winner || ""}</td>
        <td>${r.trainer || ""}</td>
        <td>${r.jockey || ""}</td>
        <td>${r.country || ""}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  yearFilter.addEventListener("change", applyFilters);
  raceFilter.addEventListener("change", applyFilters);
  winnerFilter.addEventListener("change", applyFilters);
});
