document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");
  const raceSelect    = document.getElementById("raceSelect");
  const tableBody     = document.querySelector("#resultsTable tbody");

  let results = [];

  /* ---------- LOAD DATA ---------- */

  fetch("data/hong-kong-jockeys-trainers.json")
    .then(res => res.json())
    .then(data => {

      // ALL RIDES (no finish filter)
      results = data.sort((a, b) => b.year - a.year);

      buildFilters();
      render();
    });

  /* ---------- BUILD FILTER OPTIONS ---------- */

  function buildFilters() {
    const jockeys  = new Set();
    const trainers = new Set();
    const races    = new Set();

    results.forEach(r => {
      jockeys.add(r.jockey);
      trainers.add(r.trainer);
      races.add(r.race);
    });

    [...jockeys].sort().forEach(j => {
      jockeySelect.innerHTML += `<option value="${j}">${j}</option>`;
    });

    [...trainers].sort().forEach(t => {
      trainerSelect.innerHTML += `<option value="${t}">${t}</option>`;
    });

    [...races].sort().forEach(r => {
      raceSelect.innerHTML += `<option value="${r}">${r}</option>`;
    });
  }

  /* ---------- RENDER TABLE ---------- */

  function render() {
    tableBody.innerHTML = "";

    const jockey  = jockeySelect.value;
    const trainer = trainerSelect.value;
    const race    = raceSelect.value;

    const filtered = results.filter(r => {
      return (
        (!jockey  || r.jockey === jockey) &&
        (!trainer || r.trainer === trainer) &&
        (!race    || r.race === race)
      );
    });

    if (filtered.length === 0) {
      tableBody.innerHTML =
        `<tr><td colspan="6">No matching rides.</td></tr>`;
      return;
    }

    filtered.forEach(r => {
      tableBody.innerHTML += `
        <tr>
          <td>${r.year}</td>
          <td>${r.race}</td>
          <td>${r.horse}</td>
          <td>${r.jockey}</td>
          <td>${r.trainer}</td>
          <td>${r.sp}</td>
        </tr>`;
    });
  }

  jockeySelect.addEventListener("change", render);
  trainerSelect.addEventListener("change", render);
  raceSelect.addEventListener("change", render);

});
