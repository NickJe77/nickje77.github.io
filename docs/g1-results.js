document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");
  const groups = document.querySelectorAll(".filter-group");

  const yearInput = groups[0].querySelector("input");
  const yearSelect = groups[0].querySelector("select");

  const raceInput = groups[1].querySelector("input");
  const raceSelect = groups[1].querySelector("select");

  const winnerInput = groups[2].querySelector("input");
  const winnerSelect = groups[2].querySelector("select");

  let allResults = [];

  fetch("g1-results.json", { cache: "no-store" })
    .then(r => r.json())
    .then(data => {
      allResults = data.map(r => ({
        year: r.year ?? r.Year ?? "",
        race: r.race ?? r.Race ?? "",
        track: r.track ?? r.Track ?? "",
        winner: r.winner ?? r.Winner ?? "",
        jockey: r.jockey ?? r.Jockey ?? "",
        trainer: r.trainer ?? r.Trainer ?? "",
        country: r.country ?? r.Country ?? ""
      }));

      allResults.sort((a, b) => b.year - a.year);

      populateSelect(yearSelect, [...new Set(allResults.map(r => r.year))]);
      populateSelect(raceSelect, [...new Set(allResults.map(r => r.race))]);
      populateSelect(winnerSelect, [...new Set(allResults.map(r => r.winner))]);

      render(allResults);

      [yearInput, raceInput, winnerInput].forEach(i =>
        i.addEventListener("input", () => filterOptions(i))
      );

      [yearSelect, raceSelect, winnerSelect].forEach(s =>
        s.addEventListener("change", applyFilters)
      );
    });

  function populateSelect(select, values) {
    select.innerHTML = `<option value="all">All</option>`;
    values.filter(Boolean).sort().forEach(v => {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      select.appendChild(o);
    });
    select.disabled = false;
  }

  function filterOptions(input) {
    const select = input.nextElementSibling;
    const term = input.value.toLowerCase();
    [...select.options].forEach(o => {
      o.hidden = o.value !== "all" && !o.textContent.toLowerCase().includes(term);
    });
  }

  function applyFilters() {
    let filtered = allResults;

    if (yearSelect.value !== "all")
      filtered = filtered.filter(r => String(r.year) === yearSelect.value);

    if (raceSelect.value !== "all")
      filtered = filtered.filter(r => r.race === raceSelect.value);

    if (winnerSelect.value !== "all")
      filtered = filtered.filter(r => r.winner === winnerSelect.value);

    render(filtered);
  }

  function render(rows) {
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
});
