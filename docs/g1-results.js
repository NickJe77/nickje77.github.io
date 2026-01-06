document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector(".archive-table tbody");

  if (!tbody) {
    console.error("G1 Results: table body not found");
    return;
  }

  fetch("g1-results.json")
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (!Array.isArray(data)) {
        console.error("G1 Results: JSON is not an array");
        return;
      }

      tbody.innerHTML = "";

      data.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.year || ""}</td>
          <td>${row.race || ""}</td>
          <td>${row.track || ""}</td>
          <td>${row.winner || ""}</td>
          <td>${row.country || ""}</td>
          <td>${row.trainer || ""}</td>
          <td>${row.jockey || ""}</td>
        `;
        tbody.appendChild(tr);
      });

      console.log(`G1 Results loaded: ${data.length} rows`);
    })
    .catch(err => {
      console.error("G1 Results load failed:", err);
    });
});
