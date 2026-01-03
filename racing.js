document.addEventListener("DOMContentLoaded", () => {
  fetch("g1-results.json")
    .then(response => {
      if (!response.ok) {
        throw new Error("JSON not found");
      }
      return response.json();
    })
    .then(data => {
      const tableBody = document.querySelector("#g1-table tbody");

      data.forEach(row => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
          <td>${row.year}</td>
          <td>${row.race}</td>
          <td>${row.track}</td>
          <td>${row.winner}</td>
          <td>${row.jockey}</td>
          <td>${row.trainer}</td>
          <td>${row.country}</td>
        `;

        tableBody.appendChild(tr);
      });
    })
    .catch(error => {
      console.error("G1 LOAD ERROR:", error);
    });
});

