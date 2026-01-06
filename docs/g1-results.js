document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");
  const filterGroups = document.querySelectorAll(".filter-group");

  if (!tbody || filterGroups.length < 3) {
    console.error("Filter groups or table body not found");
    return;
  }

  // Map inputs + selects
  const yearInput = filterGroups[0].querySelector("input");
  const yearSelect = filterGroups[0].querySelector("select");

  const raceInput = filterGroups[1].querySelector("input");
  const raceSelect = filterGroups[1].querySelector("select");

  const winnerInput = filterGroups[2].querySelector("input");
  const winnerSelect = filterGroups[2].querySelector("select");

  let allResults = [];

  fetch("g1-results.json", { cache: "no-store" })
    .then(r => {
      if (!r.ok) throw new Error("Failed to load g1-results.json");
      return r.json();
    })
    .then(data => {
      if (!Array.isArray(data) || data.length === 0) {
        showMessage("No Group 1 results loaded yet.");
        return;
      }

      // Normalise keys (capitalised Excel headers safe)
      allResults = data.map(r => ({
        year: r.year ?? r.Year ?? "",
        race: r.race ?? r.Race ?? "",
        track: r.track ?? r.Track ?? "",
        winner: r.winner ?? r.Winner ?? "",
        jockey: r.jockey ?? r.Jockey ?? "",
        trainer: r.trainer ?? r.Trainer ?? "",
        country: r.country ?? r.Country ?? ""
      }));

      allResults.sort((a, b) => (b.year || 0) - (a.year || 0));

      initFilter(yearSelect, yearInput, allResults.map(r => String(r.year)));
      initFilter(raceSelect, raceInput, allResults.map(r => r.race));
      initFilter(winnerSelect, winnerInput, allResults.map(r => r.winner));

      renderTable(allResults);

      yearSelect.addEventListener("change", applyFilters);
      raceSelect.addEventListener("change", applyFilters);
      winnerSelect.addEventListener("change", applyFilters);
    })
    .catch(err => {
      console.error(err);
      showMessage("Results data could not be loaded.");
    });

  function initFilter(select, input, values) {
    const uniqueValues = [...new Set(values.filter(Boolean))].sort();

    select.innerHTML = `<option value="all">All</option>`;
    uniqueValues.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    });

    select.disabled = false;

    // 🔮 Predictive filtering driven by text input
    input.addEventListener("input", () => {
      const term = input.value.toLowerCase();

      Array.from(select.options).forEach(opt => {
        if (opt.value === "all") {
          opt.hidden = false;
        } else {
          opt.hidden = !opt.textContent.toLowerCase().includes(term);
        }
      });

      // Auto-select first visible non-All option
      const firstMatch = Array.from(select.options).find(
        o => !o.hidden && o.value !== "all"
      );

      if (term && firstMatch) {
        select.value = firstMatch.value;
        select.dispatchEvent(new Event("change"));
      }

      if (!term) {
        select.value = "all";
        select.dispatchEvent(new Event("change"));
      }
    });
  }

  function applyFilters() {
    let filtered = allResults;

    if (yearSelect.value !== "all") {
      filtered = filtered.filter(r => String(r.year) === yearSelect.value);
    }

    if (raceSelect.value !== "all") {
      filtered = filtered.filter(r => r.race === raceSelect.value);
    }

    if (winnerSelect.value !== "all") {
      filtered = filtered.filter(r => r.winner === winnerSelect.value);
    }

    renderTable(filtered);
  }

  function renderTable(rows) {
    tbody.innerHTML = "";

    if (!rows.length) {
      showMessage("No results match the selected filters.");
      return;
    }

    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.year}</td>
        <td>${r.race}</td>
        <td>${r.track}</td>
        <td>${r.winner}</td>
        <td>${r.jockey}</td>
        <td>${r.trainer}</td>
        <td>${r.country}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function showMessage(msg) {
    tbody.innerHTML = "";
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 7;
    td.style.padding = "16px";
    td.style.fontStyle = "italic";
    td.style.color = "#666";
    td.textContent = msg;
    tr.appendChild(td);
    tbody.appendChild(tr);
  }
});
