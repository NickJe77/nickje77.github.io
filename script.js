document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#results-table tbody");
  const yearFilter = document.getElementById("yearFilter");
  const searchInput = document.getElementById("searchInput");

  let allData = [];

  // ✅ IMPORTANT: relative path for GitHub Pages + custom domain
  fetch("./data/g1-racing.json")
    .then(response => response.json())
    .then(data => {
      allData = data;
      populateYearFilter(data);
      renderTable(data);
    })
    .catch(error => {
      console.error("Error loading racing data:", error);
    });

  function populateYearFilter(data) {
    const years = [...new Set(data.map(item => item.year))].sort((a, b) => b - a);

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
          <td colspan="7" style="text-align:center; opacity:0.6;">
            No results found
          </td>
        </tr>
      `;
      return;
    }

    data.forEach(item => {
