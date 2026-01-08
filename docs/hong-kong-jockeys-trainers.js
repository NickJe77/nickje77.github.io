console.log("HK Jockeys & Trainers JS loaded");

document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");
  const raceSelect    = document.getElementById("raceSelect");
  const tableBody     = document.querySelector("#resultsTable tbody");

  if (!jockeySelect || !trainerSelect || !raceSelect || !tableBody) {
    console.error("Required DOM elements not found");
    return;
  }

  fetch("./data/hong-kong-jockeys-trainers.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON not found");
      return res.json();
    })
    .then(data => {
      console.log("HK data loaded:", data.length, "rows");

      buildFilters(data);
      render(data);
    })
    .catch(err => {
      console.error("HK data load failed:", err);
      tableBody.innerHTML =
        `<tr><td colspan="6">Failed to load data.</td></tr>`;
    });

  function buildFilters(data) {
    const jockeys  = new Set();
    const trainers = new Set();
    const races    = new Set();

    data.forEach(r => {
      jockeys.add(r.jockey);
      trainers.add(r.trainer);
      races.add(r.race);
    });

    jockeys.forEach(j =>
      jockeySelect.innerHTML += `<option value="${j}">${j}</option>`
    );

    trainers.forEach(t =>
      trainerSelect.innerHTML += `<option value="${t}">${t}</option>`
    );

    races.forEach(r =>
      raceSelect.innerHTML += `<option value="${r}">${r}</option>`
    );
  }

  function render(data) {
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

  jockeySelect.addEventListener("change", () => render(window.hkData));
  trainerSelect.addEventListener("change", () => render(window.hkData));
  raceSelect.addEventListener("change", () => render(window.hkData));

});
