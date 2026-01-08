document.addEventListener("DOMContentLoaded", () => {

  const jockeySelect = document.getElementById("jockeySelect");
  const trainerSelect = document.getElementById("trainerSelect");
  const raceFilter = document.getElementById("raceFilter");

  const jockeyBody = document.querySelector("#jockeyTable tbody");
  const trainerBody = document.querySelector("#trainerTable tbody");

  let results = [];

  fetch("data/hong-kong-jockeys-trainers.json")
    .then(r => r.json())
    .then(data => {
      results = data.sort((a, b) => b.year - a.year);
      buildFilters();
      autoSelectTop();
    });

  function buildFilters() {
    const jockeys = {};
    const trainers = {};
    const races = new Set();

    results.forEach(r => {
      jockeys[r.jockey] = (jockeys[r.jockey] || 0) + 1;
      trainers[r.trainer] = (trainers[r.trainer] || 0) + 1;
      races.add(r.race);
    });

    Object.entries(jockeys)
      .sort((a, b) => b[1] - a[1])
      .forEach(([name, wins]) => {
        const o = document.createElement("option");
        o.value = name;
        o.textContent = `${name} (${wins})`;
        jockeySelect.appendChild(o);
      });

    Object.entries(trainers)
      .sort((a, b) => b[1] - a[1])
      .forEach(([name, wins]) => {
        const o = document.createElement("option");
        o.value = name;
        o.textContent = `${name} (${wins})`;
        trainerSelect.appendChild(o);
      });

    [...races].sort().forEach(race => {
      const o = document.createElement("option");
      o.value = race;
      o.textContent = race;
      raceFilter.appendChild(o);
    });
  }

  function autoSelectTop() {
    jockeySelect.selectedIndex = 0;
    trainerSelect.selectedIndex = 0;
    render();
  }

  function render() {
    renderJockey();
    renderTrainer();
  }

  function raceMatch(r) {
    return !raceFilter.value || r.race === raceFilter.value;
  }

  function renderJockey() {
    jockeyBody.innerHTML = "";
    const jockey = jockeySelect.value;

    results
      .filter(r => r.jockey === jockey && raceMatch(r))
      .forEach(r => {
        jockeyBody.innerHTML += `
          <tr>
            <td>${r.year}</td>
            <td>${r.race}</td>
            <td>${r.horse}</td>
            <td>${r.trainer}</td>
            <td>${r.SP ?? ""}</td>
          </tr>`;
      });
  }

  function renderTrainer() {
    trainerBody.innerHTML = "";
    const trainer = trainerSelect.value;

    results
      .filter(r => r.trainer === trainer && raceMatch(r))
      .forEach(r => {
        trainerBody.innerHTML += `
          <tr>
            <td>${r.year}</td>
            <td>${r.race}</td>
            <td>${r.horse}</td>
            <td>${r.jockey}</td>
            <td>${r.SP ?? ""}</td>
          </tr>`;
      });
  }

  jockeySelect.addEventListener("change", render);
  trainerSelect.addEventListener("change", render);
  raceFilter.addEventListener("change", render);

});
