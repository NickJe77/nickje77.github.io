document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");

  const yearSelect = document.getElementById("yearFilter");
  const raceInput = document.getElementById("raceFilter");
  const winnerInput = document.getElementById("winnerFilter");

  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");

  let allData = [];

  fetch("breeders-cup-results.json")
    .then(res => res.json())
    .then(data => {
      allData = data.sort((a, b) => b.year - a.year);
      buildYearFilter();
      renderTable(allData);
    });

  function buildYearFilter() {
    const years = [...new Set(allData.map(r => r.year))].sort((a, b) => b - a);
    years.forEach(year => {
      const opt = document.createElement("option");
      opt.value = year;
      opt.textContent = year;
      yearSelect.appendChild(opt);
    });
  }

  function renderTable(rows) {
    tbody.innerHTML = "";
    rows.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.year}</td>
        <td>${row.race}</td>
        <td>${row.track}</td>
        <td>${row.winner}</td>
        <td>${row.jockey}</td>
        <td>${row.trainer}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function applyFilters() {
    const yearVal = yearSelect.value;
    const raceVal = raceInput.value.toLowerCase();
    const winnerVal = winnerInput.value.toLowerCase();

    const filtered = allData.filter(r => {
      return (
        (yearVal === "all" || r.year.toString() === yearVal) &&
        (raceVal === "" || r.race.toLowerCase().includes(raceVal)) &&
        (winnerVal === "" || r.winner.toLowerCase().includes(winnerVal))
      );
    });

    renderTable(filtered);
  }

  yearSelect.addEventListener("change", applyFilters);
  raceInput.addEventListener("input", () => {
    showSuggestions(raceInput, raceList, "race");
    applyFilters();
  });
  winnerInput.addEventListener("input", () => {
    showSuggestions(winnerInput, winnerList, "winner");
    applyFilters();
  });

  function showSuggestions(input, list, field) {
    const val = input.value.toLowerCase();
    list.innerHTML = "";
    if (!val) return;

    const matches = [...new Set(
      allData
        .map(r => r[field])
        .filter(v => v.toLowerCase().includes(val))
    )].slice(0, 10);

    matches.forEach(match => {
      const div = document.createElement("div");
      div.textContent = match;
      div.addEventListener("click", () => {
        input.value = match;
        list.innerHTML = "";
        applyFilters();
      });
      list.appendChild(div);
    });
  }

  document.addEventListener("click", e => {
    if (!e.target.closest(".autocomplete")) {
      raceList.innerHTML = "";
      winnerList.innerHTML = "";
    }
  });
});
