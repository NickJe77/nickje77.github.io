document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");

  const yearSelect = document.getElementById("yearSelect");
  const raceInput = document.getElementById("raceInput");
  const raceList = document.getElementById("raceList");
  const winnerInput = document.getElementById("winnerInput");
  const winnerList = document.getElementById("winnerList");

  let allResults = [];
  let allRaces = [];
  let allWinners = [];

  let selectedRace = "all";
  let selectedWinner = "all";

  fetch("breeders-cup-results.json", { cache: "no-store" })
    .then(r => r.json())
    .then(data => {
      allResults = data.map(row => ({
        year: row.year ?? row.Year ?? "",
        race: row.race ?? row.Race ?? "",
        track: row.track ?? row.Track ?? "",
        winner: row.winner ?? row.Winner ?? "",
        jockey: row.jockey ?? row.Jockey ?? "",
        trainer: row.trainer ?? row.Trainer ?? "",
        country: row.country ?? row.Country ?? ""
      }));

      allResults.sort((a, b) => (Number(b.year) || 0) - (Number(a.year) || 0));

      const years = [...new Set(allResults.map(r => String(r.year)).filter(Boolean))];
      allRaces = [...new Set(allResults.map(r => r.race).filter(Boolean))].sort();
      allWinners = [...new Set(allResults.map(r => r.winner).filter(Boolean))].sort();

      yearSelect.innerHTML = `<option value="all">All</option>`;
      years.forEach(y => {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        yearSelect.appendChild(opt);
      });
      yearSelect.disabled = false;

      yearSelect.addEventListener("change", applyFilters);

      setupAutocomplete(raceInput, raceList, allRaces, value => {
        selectedRace = value;
        applyFilters();
      });

      setupAutocomplete(winnerInput, winnerList, allWinners, value => {
        selectedWinner = value;
        applyFilters();
      });

      applyFilters();
    });

  function applyFilters() {
    let filtered = allResults;

    if (yearSelect.value !== "all") {
      filtered = filtered.filter(r => String(r.year) === yearSelect.value);
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

  function setupAutocomplete(input, list, items, onSelect) {
    let active = -1;
    let matches = [];

    input.addEventListener("input", () => open(input.value));
    input.addEventListener("focus", () => open(input.value));

    input.addEventListener("keydown", e => {
      if (!list.classList.contains("open")) return;
      if (e.key === "ArrowDown") active = Math.min(active + 1, matches.length - 1);
      if (e.key === "ArrowUp") active = Math.max(active - 1, 0);
      if (e.key === "Enter" && matches[active]) choose(matches[active]);
      paint();
    });

    document.addEventListener("click", e => {
      if (!list.contains(e.target) && e.target !== input) close();
    });

    function open(q) {
      const term = q.toLowerCase();
      matches = term
        ? items.filter(v => v.toLowerCase().startsWith(term)).slice(0, 80)
        : items.slice(0, 50);

      list.innerHTML = "";
      list.classList.add("open");

      matches.forEach(v => {
        const d = document.createElement("div");
        d.className = "autocomplete-item";
        d.textContent = v;
        d.onclick = () => choose(v);
        list.appendChild(d);
      });

      paint();
    }

    function choose(v) {
      input.value = v;
      close();
      onSelect(v);
    }

    function paint() {
      [...list.children].forEach((c, i) =>
        c.classList.toggle("active", i === active)
      );
    }

    function close() {
      list.classList.remove("open");
      list.innerHTML = "";
      active = -1;
    }
  }
});
