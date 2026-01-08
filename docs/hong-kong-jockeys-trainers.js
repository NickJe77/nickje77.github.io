/* =========================================================
   Hong Kong International Races
   Jockeys & Trainers – Parallel Tables
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

  const DATA_URL = "../data/hong-kong-results.json";

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");

  const jockeyTableBody  = document.querySelector("#jockeyTable tbody");
  const trainerTableBody = document.querySelector("#trainerTable tbody");

  if (!jockeySelect || !trainerSelect || !jockeyTableBody || !trainerTableBody) {
    console.error("HK Jockeys & Trainers: Required DOM elements not found.");
    return;
  }

  fetch(DATA_URL)
    .then(response => {
      if (!response.ok) {
        throw new Error("Failed to load HK results JSON");
      }
      return response.json();
    })
    .then(data => {
      initialiseDropdowns(data);
      bindEvents(data);
    })
    .catch(error => {
      console.error("HK Jockeys & Trainers error:", error);
    });

  /* ---------------------------------------------------------
     Initialise dropdowns
     --------------------------------------------------------- */

  function initialiseDropdowns(data) {

    const jockeys = [...new Set(
      data.map(d => d.jockey).filter(Boolean)
    )].sort();

    const trainers = [...new Set(
      data.map(d => d.trainer).filter(Boolean)
    )].sort();

    jockeys.forEach(jockey => {
      const option = document.createElement("option");
      option.value = jockey;
      option.textContent = jockey;
      jockeySelect.appendChild(option);
    });

    trainers.forEach(trainer => {
      const option = document.createElement("option");
      option.value = trainer;
      option.textContent = trainer;
      trainerSelect.appendChild(option);
    });
  }

  /* ---------------------------------------------------------
     Event bindings
     --------------------------------------------------------- */

  function bindEvents(data) {

    jockeySelect.addEventListener("change", () => {
      renderJockeyTable(data, jockeySelect.value);
    });

    trainerSelect.addEventListener("change", () => {
      renderTrainerTable(data, trainerSelect.value);
    });
  }

  /* ---------------------------------------------------------
     Render Jockey table
     --------------------------------------------------------- */

  function renderJockeyTable(data, selectedJockey) {

    jockeyTableBody.innerHTML = "";

    if (!selectedJockey) return;

    const rows = data
      .filter(d => d.jockey === selectedJockey)
      .sort((a, b) => b.year - a.year);

    rows.forEach(d => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${safe(d.year)}</td>
        <td>${safe(d.race)}</td>
        <td>${safe(d.horse)}</td>
        <td>${safe(d.trainer)}</td>
      `;

      jockeyTableBody.appendChild(tr);
    });
  }

  /* ---------------------------------------------------------
     Render Trainer table
     --------------------------------------------------------- */

  function renderTrainerTable(data, selectedTrainer) {

    trainerTableBody.innerHTML = "";

    if (!selectedTrainer) return;

    const rows = data
      .filter(d => d.trainer === selectedTrainer)
      .sort((a, b) => b.year - a.year);

    rows.forEach(d => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${safe(d.year)}</td>
        <td>${safe(d.race)}</td>
        <td>${safe(d.horse)}</td>
        <td>${safe(d.jockey)}</td>
      `;

      trainerTableBody.appendChild(tr);
    });
  }

  /* ---------------------------------------------------------
     Utility
     --------------------------------------------------------- */

  function safe(value) {
    return value !== undefined && value !== null ? value : "";
  }

});
