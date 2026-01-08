console.log("HK Jockeys & Trainers JS loaded");

document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");
  const raceSelect    = document.getElementById("raceSelect");
  const tableBody     = document.querySelector("#resultsTable tbody");

  fetch("https://thesportingalmanac.com/data/hong-kong-jockeys-trainers.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON load failed");
      return res.json();
    })
    .then(data => {
      console.log("Rows loaded:", data.length);
      populateFilters(data);
      renderTable(data);
    })
    .catch(err => {
      console.error(err);
      tableBody.innerHTML =
        `<tr><td colspan="6">Failed to load data</td></tr>`;
    });

  function populateFilters(data) {
    const jockeys = new Set();
    const trainers = new Set();
    const races = new Set();

    data.forEach(r => {
      jockeys.add(r.jockey);
      trainers.add(r.trainer);
      races.add(r.race);
    });

    jockeys.forEach(j =>
      jockeySelect.insertAdjacentHTML("beforeend",
        `<option value="${j}">${j}</option>`)
    );

    trainers.forEach(t =>
      trainerSelect.insertAdjacentHTML("beforeend",
        `<option value="${t}">${t}</option>`)
    );

    races.forEach(r =>
      raceSelect.insertAdjacentHTML("beforeend",
        `<option value="${r}">${r}</option>`)
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

  jockeySelect.addEventListener("change", () => reload());
  trainerSelect.addEventListener("change", () => reload());
  raceSelect.addEventListener("change", () => reload());

  function reload() {
    fetch("https://thesportingalmanac.com/data/hong-kong-jockeys-trainers.json")
      .then(r => r.json())
      .then(renderTable);
  }

});
