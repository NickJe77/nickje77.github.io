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

  // -------------------------
  // Helpers
  // -------------------------

  // arc.json uses UPPERCASE keys (YEAR, RACE, WINNER, TRAINER, JOCKEY).
  // Lowercase keys are accepted too, so either version of the file works.
  // Values are trimmed because some entries carry trailing spaces
  // (e.g. "PRIX DU ROND POINT ").
  function pick(row, key) {
    const v = row[key] ?? row[key.toUpperCase()];
    return v == null ? "" : String(v).trim();
  }

  // The same race appears with both a curly apostrophe (L’OPERA) and a
  // straight one (L'OPERA), so treat them as identical when matching and
  // when building the suggestion lists.
  const APOS = /[\u2018\u2019\u02BC]/g;
  const straighten = s => s.replace(APOS, "'");
  const norm = s => straighten(s).toLowerCase();

  const esc = s => String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  function normaliseRow(row) {
    const out = {
      year: parseInt(pick(row, "year"), 10) || 0,
      race: pick(row, "race"),
      winner: pick(row, "winner"),
      trainer: pick(row, "trainer"),
      jockey: pick(row, "jockey")
    };
    // Pre-computed lowercase/straight-apostrophe copies for fast filtering
    out._race = norm(out.race);
    out._winner = norm(out.winner);
    out._jockey = norm(out.jockey);
    return out;
  }

  const uniqueSorted = (values, tidy = s => s) =>
    [...new Set(values.filter(Boolean).map(tidy))].sort((a, b) => a.localeCompare(b));

  // -------------------------
  // Load data
  // -------------------------

  // arc.json MUST be in same folder as arc.html
  fetch("arc.json")
    .then(res => res.json())
    .then(data => {
      console.log("Rows loaded:", data.length);

      // Newest year first (sort is stable, so file order is kept within a year)
      allRows = data.map(normaliseRow).sort((a, b) => b.year - a.year);

      populateFilters(allRows);
      renderTable(allRows);
    })
    .catch(err => {
      console.error("Arc JSON load FAILED:", err);
      tbody.innerHTML =
        '<tr><td colspan="5" style="text-align:center;padding:18px;">Could not load the archive data.</td></tr>';
    });

  function populateFilters(data) {
    const years = [...new Set(data.map(r => r.year).filter(Boolean))].sort((a, b) => b - a);
    const races = uniqueSorted(data.map(r => r.race), straighten);
    const winners = uniqueSorted(data.map(r => r.winner));
    const jockeys = uniqueSorted(data.map(r => r.jockey));

    // Append after the existing "All" option
    yearFilter.insertAdjacentHTML(
      "beforeend",
      years.map(y => `<option value="${y}">${y}</option>`).join("")
    );
    raceList.innerHTML = races.map(r => `<option value="${esc(r)}">`).join("");
    winnerList.innerHTML = winners.map(w => `<option value="${esc(w)}">`).join("");
    jockeyList.innerHTML = jockeys.map(j => `<option value="${esc(j)}">`).join("");
  }

  function applyFilters() {
    const y = yearFilter.value;
    const r = norm(raceFilter.value.trim());
    const w = norm(winnerFilter.value.trim());
    const j = norm(jockeyFilter.value.trim());

    const filtered = allRows.filter(row =>
      (!y || row.year == y) &&
      (!r || row._race.includes(r)) &&
      (!w || row._winner.includes(w)) &&
      (!j || row._jockey.includes(j))
    );

    renderTable(filtered);
  }

  function renderTable(rows) {
    tbody.innerHTML = rows.map(r => `
        <tr>
          <td>${r.year || ""}</td>
          <td>${esc(r.race)}</td>
          <td>${esc(r.winner)}</td>
          <td>${esc(r.trainer)}</td>
          <td>${esc(r.jockey)}</td>
        </tr>
      `).join("");
  }

  yearFilter.addEventListener("change", applyFilters);
  raceFilter.addEventListener("input", applyFilters);
  winnerFilter.addEventListener("input", applyFilters);
  jockeyFilter.addEventListener("input", applyFilters);
});
