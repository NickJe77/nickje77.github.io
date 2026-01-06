document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");
  const filterSelects = document.querySelectorAll(".filters select");

  if (!tbody || filterSelects.length < 3) {
    console.error("Required elements not found");
    return;
  }

  const yearSelect = filterSelects[0];
  const raceSelect = filterSelects[1];
  const horseSelect = filterSelects[2];

  let allResults = [];

  fetch("g1-results.json", { cache: "no-store" })
    .then(response => {
      if (!response.ok) {
        throw new Error("Failed to load g1-results.json");
      }
      return response.json();
    })
    .then(data => {
      if (!Array.isArray(data) || data.length === 0) {
        showMessage("No Group 1 results loaded yet.");
        return;
      }

      // Normalise keys (handles Excel capitalisation)
      allResults = data.map(row => ({
        year: row.year ?? row.Year ?? "",
        race: row.race ?? row.Race ?? "",
        track: row.track ?? row.Track ?? "",
        winner: row.winner ?? row.Winner ?? "",
        jockey: row.jockey ?? row.Jockey ?? "",
        trainer: row.trainer ?? row.Trainer ?? "",
        country: row.country ?? row.Country ?? ""
      }));

      // Sort newest → oldest
      allResults.sort((a, b) => (b.year || 0) - (a.year || 0));

      populateYearFilter();
      populateRaceFilter();
      populateHorseFilter();
      renderTable(allResults);
    })
    .catch(error => {
      console.error("G1 results load error:", error);
      showMessage("Results data could not be loaded.");
    });

  function populateYearFilter() {
    const years = [...new Set(allResults.map(r => r.year).filter(Boolean))];

    yearSelect.innerHTML = `<option value="all">All</option>`;
    years.forEach(year => {
      const opt = document.createElement("option");
      opt.value = year;
      opt.textContent = year;
      yearSelect.appendChild(opt);
    });

    yearSelect.disabled = false;
    yearSelect.addEventListener("change", applyFilters);
  }

  function populateRaceFilter() {
    const races = [...new Set(allResults.map(r => r.race).filter(Boolean))].sort();

    raceSelect.innerHTML = `<option value="all">All</option>`;
    races.forEach(race => {
      const opt = document.createElement("option");
      opt.value = race;
      opt.textContent = race;
      raceSelect.appendChild(opt);
    });

    raceSelect.disabled = false;
    raceSelect.addEventListener("change", applyFilters);
  }

  function populateHorseFilter() {
    const horses = [...new Set(allResults.map(r => r.winner).filter(Boolean))].sort();

    horseSelect.innerHTML = `<option value="all">All</option>`;
    horses.forEach(horse => {
      const opt = document.createElement("option");
      opt.value = horse;
      opt.textContent = horse;
      horseSelect.appendChild(opt);
    });

    horseSelect.disabled = false;
    horseSelect.addEventListener("change", applyFilters);
  }

  function applyFilters() {
    const selectedYear = yearSelect.value;
    const selectedRace = raceSelect.value;
    const selectedHorse = horseSelect.value;

    let filtered = allResults;

    if (selectedYear !== "all") {
      filtered = filtered.filter(r => String(r.year) === selectedYear);
    }

    if (selectedRace !== "all") {
      filtered = filtered.filter(r => r.race === selectedRace);
    }

    if (selectedHorse !== "all") {
      filtered = filtered.filter(r => r.winner === selectedHorse);
    }

    renderTable(filtered);
  }

  function renderTable(results) {
    tbody.innerHTML = "";

    if (results.length === 0) {
      showMessage("No results match the selected filters.");
      return;
    }

    results.forEach(row => {
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

  function showMessage(message) {
    tbody.innerHTML = "";
    const tr = document.createElement("tr");
    const td = document.createElement("td");

    td.colSpan = 7;
    td.style.padding = "16px";
    td.style.fontStyle = "italic";
    td.style.color = "#666";
    td.textContent = message;

    tr.appendChild(td);
    tbody.appendChild(tr);
  }
});
