document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");

  const yearSelect = document.getElementById("yearSelect");

  const raceInput = document.getElementById("raceInput");
  const raceList = document.getElementById("raceList");

  const winnerInput = document.getElementById("winnerInput");
  const winnerList = document.getElementById("winnerList");

  if (!tbody || !yearSelect || !raceInput || !raceList || !winnerInput || !winnerList) {
    console.error("Required elements not found");
    return;
  }

  let allResults = [];
  let allRaces = [];
  let allWinners = [];

  let selectedRace = "all";
  let selectedWinner = "all";

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
      allResults.sort((a, b) => (Number(b.year) || 0) - (Number(a.year) || 0));

      // Build unique lists
      const years = [...new Set(allResults.map(r => String(r.year)).filter(Boolean))];
      allRaces = [...new Set(allResults.map(r => r.race).filter(Boolean))].sort();
      allWinners = [...new Set(allResults.map(r => r.winner).filter(Boolean))].sort();

      // Populate year dropdown (newest first)
      yearSelect.innerHTML = `<option value="all">All</option>`;
      years.forEach(y => {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        yearSelect.appendChild(opt);
      });
      yearSelect.disabled = false;

      // Wire up filters
      yearSelect.addEventListener("change", applyFilters);

      setupAutocomplete({
        input: raceInput,
        list: raceList,
        getItems: () => allRaces,
        onSelect: (value) => {
          selectedRace = value;
          applyFilters();
        },
        onClear: () => {
          selectedRace = "all";
          applyFilters();
        }
      });

      setupAutocomplete({
        input: winnerInput,
        list: winnerList,
        getItems: () => allWinners,
        onSelect: (value) => {
          selectedWinner = value;
          applyFilters();
        },
        onClear: () => {
          selectedWinner = "all";
          applyFilters();
        }
      });

      // Initial render
      applyFilters();
    })
    .catch(err => {
      console.error("G1 load error:", err);
      showMessage("Results data could not be loaded.");
    });

  function applyFilters() {
    const selectedYear = yearSelect.value;

    let filtered = allResults;

    if (selectedYear !== "all") {
      filtered = filtered.filter(r => String(r.year) === selectedYear);
    }

    if (selectedRace !== "all") {
      filtered = filtered.filter(r => r.race === selectedRace);
    }

    if (selectedWinner !== "all") {
      filtered = filtered.filter(r => r.winner === selectedWinner);
    }

    renderTable(filtered);
  }

  function renderTable(rows) {
    tbody.innerHTML = "";

    if (!rows || rows.length === 0) {
      showMessage("No results match the selected filters.");
      return;
    }

    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.year ?? ""}</td>
        <td>${r.race ?? ""}</td>
        <td>${r.track ?? ""}</td>
        <td>${r.winner ?? ""}</td>
        <td>${r.jockey ?? ""}</td>
        <td>${r.trainer ?? ""}</td>
        <td>${r.country ?? ""}</td>
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

  // ✅ Proper predictive autocomplete:
  // - filters by "starts with" (V → VI → VIA → VIA␠ → VIA S)
  // - click to select before full typing
  // - arrow keys + enter work
  // - includes "All" at the top to clear
  function setupAutocomplete({ input, list, getItems, onSelect, onClear }) {
    let activeIndex = -1;
    let currentMatches = [];

    input.addEventListener("input", () => {
      const q = input.value;
      if (!q) {
        closeList();
        onClear();
        return;
      }
      openWithQuery(q);
    });

    input.addEventListener("focus", () => {
      // On focus, show top items if empty, or filtered if has text
      if (!input.value) {
        openWithQuery("");
      } else {
        openWithQuery(input.value);
      }
    });

    input.addEventListener("keydown", (e) => {
      if (!list.classList.contains("open")) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, currentMatches.length - 1);
        paintActive();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        paintActive();
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (activeIndex >= 0 && currentMatches[activeIndex]) {
          choose(currentMatches[activeIndex]);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        closeList();
      }
    });

    // Click outside closes
    document.addEventListener("click", (e) => {
      if (e.target === input || list.contains(e.target)) return;
      closeList();
    });

    // Click on item
    list.addEventListener("click", (e) => {
      const item = e.target.closest(".autocomplete-item");
      if (!item) return;

      const value = item.getAttribute("data-value");
      if (value === "__ALL__") {
        input.value = "";
        closeList();
        onClear();
        return;
      }

      choose(value);
    });

    function openWithQuery(query) {
      const raw = getItems();
      const q = String(query || "").toLowerCase();

      // Starts-with match, space included naturally
      // If query is empty, show a manageable slice
      let matches;
      if (!q) {
        matches = raw.slice(0, 50);
      } else {
        matches = raw.filter(v => String(v).toLowerCase().startsWith(q)).slice(0, 80);
      }

      renderList(matches, q);
      list.classList.add("open");
    }

    function renderList(matches, q) {
      list.innerHTML = "";
      activeIndex = -1;

      // "All" at top
      const allItem = document.createElement("div");
      allItem.className = "autocomplete-item muted";
      allItem.textContent = "All";
      allItem.setAttribute("data-value", "__ALL__");
      list.appendChild(allItem);

      if (matches.length === 0) {
        const none = document.createElement("div");
        none.className = "autocomplete-item muted";
        none.textContent = q ? "No matches" : "Type to search…";
        none.setAttribute("data-value", "");
        list.appendChild(none);
        currentMatches = [];
        return;
      }

      currentMatches = matches;

      matches.forEach((text) => {
        const div = document.createElement("div");
        div.className = "autocomplete-item";
        div.textContent = text;
        div.setAttribute("data-value", text);
        list.appendChild(div);
      });
    }

    function paintActive() {
      const items = Array.from(list.querySelectorAll(".autocomplete-item"))
        .filter(el => el.getAttribute("data-value") !== "__ALL__" && !el.classList.contains("muted"));

      items.forEach(el => el.classList.remove("active"));
      if (activeIndex >= 0 && items[activeIndex]) {
        items[activeIndex].classList.add("active");
        items[activeIndex].scrollIntoView({ block: "nearest" });
      }
    }

    function choose(value) {
      input.value = value;
      closeList();
      onSelect(value);
    }

    function closeList() {
      list.classList.remove("open");
      list.innerHTML = "";
      activeIndex = -1;
      currentMatches = [];
    }
  }
});
