document.addEventListener("DOMContentLoaded", () => {
  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");
  const tbody = document.querySelector(".archive-table tbody");

  let data = [];

  fetch("data/hong-kong-results.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON not found");
      return res.json();
    })
    .then(json => {
      data = json.sort((a, b) => b.year - a.year);
      populateYears();
      render(data);
    })
    .catch(err => console.error("Hong Kong load error:", err));

  function populateYears() {
    const years = [...new Set(data.map(d => d.year))].sort((a, b) => b - a);
    years.forEach(y => {
      const opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      yearFilter.appendChild(opt);
    });
  }

  function render(rows) {
    tbody.innerHTML = "";
    rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.year}</td>
        <td>${r.race}</td>
        <td>${r.winner}</td>
        <td>${r.trainer}</td>
        <td>${r.jockey}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function filter() {
    const y = yearFilter.value;
    const r = raceFilter.value.toLowerCase();
    const w = winnerFilter.value.toLowerCase();

    const filtered = data.filter(d =>
      (!y || d.year == y) &&
      (!r || d.race.toLowerCase().includes(r)) &&
      (!w || d.winner.toLowerCase().includes(w))
    );

    render(filtered);
  }

  yearFilter.addEventListener("change", filter);
  raceFilter.addEventListener("input", filter);
  winnerFilter.addEventListener("input", filter);
});
