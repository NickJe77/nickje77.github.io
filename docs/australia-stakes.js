const DATA_URL = "/data/australia-stakes.json";

let allRows = [];

fetch(DATA_URL)
  .then(res => res.json())
  .then(data => {
    allRows = data;
    buildYearFilter(data);
    renderTable(data);
  })
  .catch(err => console.error("JSON load failed:", err));

function cleanNumber(val) {
  if (!val) return "";
  return parseFloat(String(val).replace(/[^0-9.]/g, ""));
}

function renderTable(rows) {

  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";

  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.date || ""}</td>
      <td>${r.track || ""}</td>
      <td>${r.grade || ""}</td>
      <td>${r.distance || ""}</td>
      <td>${r.winner || ""}</td>
      <td>${cleanNumber(r.margin)}</td>
      <td>${cleanNumber(r.sp)}</td>
      <td>${r["race grade"] || ""}</td>
      <td>${r.jockey || ""}</td>
      <td>${r.trainer || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

/* -------- FILTER CONTROLS -------- */

function buildYearFilter(data) {
  const years = new Set();

  data.forEach(r => {
    if (r.date) years.add(r.date.substring(0,4));
  });

  const yearSelect = document.getElementById("yearFilter");
  [...years].sort().reverse().forEach(y => {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    yearSelect.appendChild(opt);
  });
}

function applyFilters() {

  const year = document.getElementById("yearFilter").value;
  const winner = document.getElementById("winnerSearch").value.toLowerCase();
  const track = document.getElementById("trackFilter").value.toLowerCase();

  const filtered = allRows.filter(r => {

    const matchYear = year === "" || (r.date && r.date.startsWith(year));
    const matchWinner = winner === "" || (r.winner && r.winner.toLowerCase().includes(winner));
    const matchTrack = track === "" || (r.track && r.track.toLowerCase().includes(track));

    return matchYear && matchWinner && matchTrack;
  });

  renderTable(filtered);
}
