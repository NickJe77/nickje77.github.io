document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");
  const selects = document.querySelectorAll(".filters select");

  if (!tbody || selects.length < 3) {
    console.error("Required elements not found (.filters select or #results-body)");
    return;
  }

  const yearSelect = selects[0];
  const raceSelect = selects[1];
  const winnerSelect = selects[2];

  let allResults = [];

  fetch("g1-results.json", { cache: "no-store" })
    .then(response => {
      if (!response.ok) throw new Error("Failed to load g1-results.json");
      return response.json();
    })
    .then(data => {
      if (!Array.isArray(data) || data.length === 0) {
        showMessage("No Group 1 results loaded yet.");
        return;
      }

      // Normalise keys (supports Excel capitalisation)
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
      populateWinnerFilter();
      renderTable(allResults);

      // Make the EXISTING selects type-to-search (contains match)
      enableTypeAhead(yearSelect);
      enableTypeAhead(raceSelect);
      enableTypeAhead(winnerSelect);

      // Filters apply on change
      yearSelect.addEventListener("change", applyFilters);
      raceSelect.addEventListener("change", applyFilters);
      winnerSelect.addEventListener("change", applyFilters);
    })
    .catch(error => {
      console.error("G1 results load error:", error);
      showMessage("Results data could not be loaded.");
    });

  function populateYearFilter() {
    const years = [...new Set(allResults.map(r => r.year).filter(Boolean))];

    yearSelect.innerHTML = `<option value="all">All</option>`;
    years.forEach(y => {
      const opt = document.createElement("option");
      opt.value = String(y);
      opt.textContent = String(y);
      yearSelect.appendChild(opt);
    });

    yearSelect.disabled = false;
  }

  function populateRaceFilter() {
    const races = [...new Set(allResults.map(r => r.race).filter(Boolean))].sort();

    raceSelect.innerHTML = `<option value="all">All</option>`;
    races.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      raceSelect.appendChild(opt);
    });

    raceSelect.disabled = false;
  }

  function populateWinnerFilter() {
    const winners = [...new Set(allResults.map(r => r.winner).filter(Boolean))].sort();

    winnerSelect.innerHTML = `<option value="all">All</option>`;
    winners.forEach(w => {
      const opt = document.createElement("option");
      opt.value = w;
      opt.textContent = w;
      winnerSelect.appendChild(opt);
    });

    winnerSelect.disabled = false;
  }

  function applyFilters() {
    const y = yearSelect.value;
    const r = raceSelect.value;
    const w = winnerSelect.value;

    let filtered = allResults;

    if (y !== "all") filtered = filtered.filter(x => String(x.year) === y);
    if (r !== "all") filtered = filtered.filter(x => x.race === r);
    if (w !== "all") filtered = filtered.filter(x => x.winner === w);

    renderTable(filtered);
  }

  function renderTable(results) {
    tbody.innerHTML = "";

    if (!results || results.length === 0) {
      showMessage("No results match the selected filters.");
      return;
    }

    results.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.year ?? ""}</td>
        <td>${row.race ?? ""}</td>
        <td>${row.track ?? ""}</td>
        <td>${row.winner ?? ""}</td>
        <td>${row.jockey ?? ""}</td>
        <td>${row.trainer ?? ""}</td>
        <td>${row.country ?? ""}</td>
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

  // ✅ Type-ahead for existing <select> elements (contains match)
  function enableTypeAhead(selectEl) {
    let buffer = "";
    let timer = null;

    selectEl.addEventListener("keydown", (e) => {
      // Ignore control keys
      if (e.key.length !== 1) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      buffer += e.key;
      const query = buffer.toLowerCase();

      // Find first option that CONTAINS the typed buffer (skip "All" if not matching)
      const options = Array.from(selectEl.options);
      const match = options.find(opt =>
        opt.value !== "" &&
        opt.value !== null &&
        opt.textContent &&
        opt.textContent.toLowerCase().includes(query)
      );

      if (match) {
        selectEl.value = match.value;
        // Trigger filtering immediately
        selectEl.dispatchEvent(new Event("change"));
      }

      // Reset buffer after a short pause
      clearTimeout(timer);
      timer = setTimeout(() => {
        buffer = "";
      }, 700);
    });

    // Clear buffer when select loses focus
    selectEl.addEventListener("blur", () => {
      buffer = "";
      clearTimeout(timer);
    });
  }
});
