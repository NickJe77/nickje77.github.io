/* =========================================================
   HONG KONG INTERNATIONAL RACES
   JOCKEYS & TRAINERS
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect  = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");

  const jockeyTableBody  = document.querySelector("#jockeyTable tbody");
  const trainerTableBody = document.querySelector("#trainerTable tbody");

  let results = [];

  /* ---------- LOAD DATA ---------- */

  fetch("data/hong-kong-jockeys-trainers.json")
    .then(res => {
      if (!res.ok) {
        throw new Error("Failed to load hong-kong-jockeys-trainers.json");
      }
      return res.json();
    })
    .then(data => {
      results = data;

      // newest → oldest
      results.sort((a, b) => b.year - a.year);

      buildDropdowns(results);
    })
    .catch(err => {
      console.error("HK Jockeys & Trainers load error:", err);
    });

  /* ---------- BUILD DROPDOWNS ---------- */

  function buildDropdowns(data) {

    const jockeys = [...new Set(data.map(r => r.jockey))].sort();
    const trainers = [...new Set(data.map(r => r.trainer))].sort();

    jockeys.forEach(j => {
      const opt = document.createElement("option");
      opt.value = j;
      opt.textContent = j;
      jockeySelect.appendChild(opt);
    });

    trainers.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      trainerSelect.appendChild(opt);
    });
  }

  /* ---------- EVENTS ---------- */

  jockeySelect.addEventListener("change", () => {
    renderJockeyTable(jockeySelect.value);
  });

  trainerSelect.addEventListener("change", () => {
    renderTrainerTable(trainerSelect.value);
  });

  /* ---------- RENDER JOCKEY TABLE ---------- */

  function renderJockeyTable(jockey) {

    jockeyTableBody.innerHTML = "";

    if (!jockey) return;

    const filtered = results.filter(r => r.jockey === jockey);

    filtered.forEach(r => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${r.year}</td>
        <td>${r.race}</td>
        <td>${r.horse}</td>
        <td>${r.trainer}</td>
        <td>${r.SP ?? ""}</td>
      `;

      jockeyTableBody.appendChild(tr);
    });
  }

  /* ---------- RENDER TRAINER TABLE ---------- */

  function renderTrainerTable(trainer) {

    trainerTableBody.innerHTML = "";

    if (!trainer) return;

    const filtered = results.filter(r => r.trainer === trainer);

    filtered.forEach(r => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${r.year}</td>
        <td>${r.race}</td>
        <td>${r.horse}</td>
        <td>${r.jockey}</td>
        <td>${r.SP ?? ""}</td>
      `;

      trainerTableBody.appendChild(tr);
    });
  }

});
