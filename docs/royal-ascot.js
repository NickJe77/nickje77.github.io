/* Royal Ascot Archive — royal-ascot.js
   Data source: royal-ascot-results.json (same directory)
   To add new results: edit royal-ascot-results.json only.
*/

(function () {
  const tbody = document.querySelector("tbody");
  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");
  const jockeyFilter = document.getElementById("jockeyFilter");
  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");
  const jockeyList = document.getElementById("jockeyList");

  let DATA = [];

  function normalize(r) {
    return {
      year:    r.YEAR    || r.year,
      race:    (r.RACE    || r.race    || "").trim(),
      winner:  (r.WINNER  || r.winner  || "").trim(),
      trainer: (r.TRAINER || r.trainer || "").trim(),
      jockey:  (r.JOCKEY  || r.jockey  || "").trim(),
      sp:      (r.SP      || r.sp      || "").trim()
    };
  }

  function populate() {
    const years = [...new Set(DATA.map(r => r.year))].sort((a, b) => b - a);
    years.forEach(y => {
      const o = document.createElement("option");
      o.value = y; o.textContent = y;
      yearFilter.appendChild(o);
    });

    const fill = (list, field) => {
      [...new Set(DATA.map(r => r[field]).filter(Boolean))].sort()
        .forEach(v => { const o = document.createElement("option"); o.value = v; list.appendChild(o); });
    };
    fill(raceList, "race");
    fill(winnerList, "winner");
    fill(jockeyList, "jockey");
  }

  function render() {
    const year   = yearFilter.value;
    const race   = raceFilter.value.toLowerCase().trim();
    const winner = winnerFilter.value.toLowerCase().trim();
    const jockey = jockeyFilter.value.toLowerCase().trim();

    const filtered = DATA.filter(r =>
      (!year   || r.year == year) &&
      (!race   || r.race.toLowerCase().includes(race)) &&
      (!winner || r.winner.toLowerCase().includes(winner)) &&
      (!jockey || r.jockey.toLowerCase().includes(jockey))
    ).sort((a, b) => b.year - a.year || a.race.localeCompare(b.race));

    tbody.innerHTML = filtered.length
      ? filtered.map(r => `<tr>
          <td>${r.year}</td>
          <td>${r.race}</td>
          <td><strong>${r.winner}</strong></td>
          <td>${r.trainer}</td>
          <td>${r.jockey}</td>
          <td>${r.sp}</td>
        </tr>`).join("")
      : `<tr><td colspan="6" style="text-align:center;color:#888;padding:24px">No results match your filters.</td></tr>`;
  }

  yearFilter.addEventListener("change", render);
  raceFilter.addEventListener("input", render);
  winnerFilter.addEventListener("input", render);
  jockeyFilter.addEventListener("input", render);

  fetch("royal-ascot-results.json")
    .then(r => {
      if (!r.ok) throw new Error("Could not load results data");
      return r.json();
    })
    .then(json => {
      DATA = json.map(normalize);
      populate();
      render();
    })
    .catch(err => {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#c00;padding:24px">
        Failed to load results. ${err.message}
      </td></tr>`;
    });
})();
