/* =========================================================
   Hong Kong International Races
   Jockeys & Trainers – Parallel Tables (SP)
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

  const DATA_URL = "../data/hong-kong-jockeys-trainers.json";

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");

  const jockeyTableBody  = document.querySelector("#jockeyTable tbody");
  const trainerTableBody = document.querySelector("#trainerTable tbody");

  if (!jockeySelect || !trainerSelect || !jockeyTableBody || !trainerTableBody) {
    console.error("HK Jockeys & Trainers: Required DOM elements not found.");
    return;
  }

  fetch(DATA_URL)
    .then(r => {
      if (!r.ok) throw new Error("Failed to load HK J&T JSON");
      return r.json();
    })
    .then(data => {
      populateDropdowns(data);
      bindEvents(data);
    })
    .catch(err => console.error(err));

  function populateDropdowns(data) {

    const jockeys = [...new Set(data.map(d => d.jockey).filter(Boolean))].sort();
    const trainers = [...new Set(data.map(d => d.trainer).filter(Boolean))].sort();

    jockeys.forEach(j => {
      const o = document.createElement("option");
      o.value = j;
      o.textContent = j;
      jockeySelect.appendChild(o);
    });

    trainers.forEach(t => {
      const o = document.createElement("option");
      o.value = t;
      o.textContent = t;
      trainerSelect.appendChild(o);
    });
  }

  function bindEvents(data) {
    jockeySelect.addEventListener("change", () =>
      renderJockey(data, jockeySelect.value)
    );

    trainerSelect.addEventListener("change", () =>
      renderTrainer(data, trainerSelect.value)
    );
  }

  function renderJockey(data, jockey) {

    jockeyTableBody.innerHTML = "";
    if (!jockey) return;

    data
      .filter(d => d.jockey === jockey)
      .sort((a, b) => b.year - a.year)
      .forEach(d => {
        jockeyTableBody.innerHTML += `
          <tr>
            <td>${safe(d.year)}</td>
            <td>${safe(d.race)}</td>
            <td>${safe(d.horse)}</td>
            <td>${safe(d.trainer)}</td>
            <td>${safe(d.SP)}</td>
          </tr>`;
      });
  }

  function renderTrainer(data, trainer) {

    trainerTableBody.innerHTML = "";
    if (!trainer) return;

    data
      .filter(d => d.trainer === trainer)
      .sort((a, b) => b.year - a.year)
      .forEach(d => {
        trainerTableBody.innerHTML += `
          <tr>
            <td>${safe(d.year)}</td>
            <td>${safe(d.race)}</td>
            <td>${safe(d.horse)}</td>
            <td>${safe(d.jockey)}</td>
            <td>${safe(d.SP)}</td>
          </tr>`;
      });
  }

  function safe(v) {
    return v !== undefined && v !== null ? v : "";
  }

});
