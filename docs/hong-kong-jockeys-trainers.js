/* =========================================================
   HK INTERNATIONAL RACES – JOCKEYS & TRAINERS (ALL RIDES)
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");
  const raceSelect    = document.getElementById("raceSelect");
  const tableBody     = document.querySelector("#resultsTable tbody");

  let allData = [];

  fetch("https://thesportingalmanac.com/data/hong-kong-jockeys-trainers.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON fetch failed");
      return res.json();
    })
    .then(data => {
      allData = data;
      buildFilters(allData);
      renderTable(allData);
    })
    .catch(err => {
      console.error(err);
      tableBody.innerHTML =
        `<tr><td colspan="6">Failed to load data</td></tr>`;
    });

  function buildFilters(data) {
    const jockeys  = new Set();
    const trainers = new Set();
    const races    = new Set();

    data.forEach(r => {
      if (r.jockey)  jockeys.add(r.jockey);
      if (r.trainer) trainers.add(r.trainer);
      if (r.race)    races.add(r.race);
    });

    [...jockeys].sort().forEach(j =>
      jockeySelect.add(new Option(j, j))
    );

    [...trainers].sort().forEach(t =>
      trainerSelect.add(new Option(t, t))
    );

    [...races].sort().forEach(r =>
      raceSelect.add(new Option(r, r))
    );
  }

  function renderTable(data) {
    tableBody.innerHTML = "";

    const j = jockeySelect.value;
    const t = trainerSelect.value;
    const r = raceSelect.value;

    const filtered = data.filter(row =>
      (!j || row.jockey === j) &&
      (!t || row.trainer === t) &&
      (!r || row.race === r)
    );

    if (!filtered.length) {
      tableBody.innerHTML =
        `<tr><td colspan="6">No matching rides</td></tr>`;
      return;
    }

    filtered.forEach(row => {
      tableBody.insertAdjacentHTML("beforeend", `
        <tr>
          <td>${row.year}</td>
          <td>${row.race}</td>
          <td>${row.horse}</td>
          <td>${row.jockey}</td>
          <td>${row.trainer}</td>
          <td>${row.sp || ""}</td>
        </tr>
      `);
    });
  }

  jockeySelect.addEventListener("change", () => renderTable(allData));
  trainerSelect.addEventListener("change", () => renderTable(allData));
  raceSelect.addEventListener("change", () => renderTable(allData));

});
