let data = [];

const tableBody = document.getElementById("tableBody");
const yearFilter = document.getElementById("yearFilter");
const searchInput = document.getElementById("searchInput");

fetch("data/breeders-cup.json")
  .then(res => res.json())
  .then(json => {
    data = json;
    populateYearFilter();
    renderTable();
  })
  .catch(err => {
    console.error("Breeders’ Cup data load error:", err);
  });

function populateYearFilter() {
  const years = [...new Set(data.map(r => r.year))].sort((a, b) => b - a);
  years.forEach(year => {
    const opt = document.createElement("option");
    opt.value = year;
    opt.textContent = year;
    yearFilter.appendChild(opt);
  });
}

function renderTable() {
  const year = yearFilter.value;
  const search = searchInput.value.toLowerCase();

  tableBody.innerHTML = "";

  data
    .filter(r =>
      (!year || r.year == year) &&
      r.race.toLowerCase().includes(search)
    )
    .forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${r.year}</td>
        <td>${r.race}</td>
        <td>${r.track}</td>
        <td>${r.winner}</td>
        <td>${r.jockey}</td>
        <td>${r.trainer}</td>
      `;
      tableBody.appendChild(tr);
    });
}

yearFilter.addEventListener("change", renderTable);
searchInput.addEventListener("input", renderTable);

