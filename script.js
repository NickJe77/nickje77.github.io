document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#racingTable tbody");
  if (!tableBody) return;

  const yearFilter = document.getElementById("yearFilter");
  const raceSearch = document.getElementById("raceSearch");

  let racingData = [];

  fetch("./data/g1-racing.json")
    .then(res => res.json())
    .then(data => {
      racingData = data;

      populateYearFilter(data);
      renderTable(data); // show all races by default
    });

  function populateYearFilter(data) {
    const years = [...new Set(data.map(r => r.year))]
      .sort((a, b) => b - a);

    years.forEach(year => {
      const option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      yearFilter.appendChild(option);
    });
  }

  function renderTable(data) {
    tableBody.innerHTML = "";

    if (data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="opacity:0.6;">
            No races match your filters
          </td>
        </tr>
      `;
      return;
    }

    data.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.year}</td>
        <td>${row.race}</td>
        <td>${row.country}</td>
        <td>${row.track}</td>
        <td>${row.winner}</td>
        <td>${row.jockey}</td>
