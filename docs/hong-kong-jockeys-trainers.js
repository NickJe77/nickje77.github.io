/* =========================================================
   HONG KONG INTERNATIONAL RACES
   JOCKEYS & TRAINERS – ALL RIDES
   ========================================================= */

console.log("HK Jockeys & Trainers JS loaded");

document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");
  const raceSelect    = document.getElementById("raceSelect");
  const tableBody     = document.querySelector("#resultsTable tbody");

  let allData = [];

  /* ---------- LOAD DATA ---------- */

  fetch("/data/hong-kong-jockeys-trainers.json")
    .then(response => {
      if (!response.ok) {
        throw new Error("JSON fetch failed");
      }
      return response.json();
    })
    .then(data => {
      console.log("HK data rows:", data.length);

      allData = data.sort((a, b) => b.year - a.year);

      buildFilters(allData);
      renderTable(allData);
    })
    .catch(error => {
      console.error("HK load error:", error);
      tableBody.innerHTML =
        `<tr><td colspan="6">Unable to load data.</td></tr>`;
    });

  /* ---------- BUILD FILTERS ---------- */

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
      jockeySelect.innerHTML += `<option value="${j}">${j}</option>`
    );

    [...trainers].sort().forEach(t =>
      trainerSelect.innerHTML += `<option value="${t}">${t}</option>`
    );

    [...races].sort().forEach(r =>
      raceSelect.innerHTML += `<option value="${r}">${r}</option>`
    );
  }

  /* ---------- FILTER + RENDER ---------- */

  function renderTable(data) {
    tableBody.innerHTML = "";

    const jockey  = jockeySelect.value;
    const trainer = trainerSelect.value;
    const race    = raceSelect.value;

    const filtered = data.filter(r =>
      (!jockey  || r.jockey === jockey) &&
      (!trainer || r.trainer === trainer) &&
      (!race    || r.race === race)
    );

    if (filtered.length === 0) {
      tableBody.innerHTML =
        `<tr><td colspan="6">No matching rides.</td></tr>`;
      return;
    }

    filtered.forEach(r => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${r.year}</td>
        <td>${r.race}</td>
        <td>${r.horse}</td>
        <td>${r.jockey}</td>
        <td>${r.trainer}</td>
        <td>${r.sp || ""}</td>
      `;

      tableBody.appendChild(row);
    });
  }

  /* ---------- EVENTS ---------- */

  jockeySelect.addEventListener("change", () => renderTable(allData));
  trainerSelect.addEventListener("change", () => renderTable(allData));
  raceSelect.addEventListener("change", () => renderTable(allData));

});
