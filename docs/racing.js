document.addEventListener("DOMContentLoaded", () => {
  fetch("g1-results.json")
    .then(response => {
      if (!response.ok) {
        throw new Error("Failed to load g1-results.json");
      }
      return response.json();
    })
    .then(data => {
      const tbody = document.querySelector("#g1-table tbody");
      tbody.innerHTML = "";

      data.forEach(item => {
        const row = document.createElement("tr");

        row.innerHTML = `
          <td>${item.year}</td>
          <td>${item.race}</td>
          <td>${item.track}</td>
          <td>${item.winner}</td>
          <td>${item.jockey}</td>
          <td>${item.trainer}</td>
          <td>${item.country}</td>
        `;

        tbody.appendChild(row);
      });
    })
    .catch(err => {
      console.error("G1 TABLE ERROR:", err);
      document.body.insertAdjacentHTML(
        "beforeend",
        "<p style='color:red'>Failed to load G1 results.</p>"
      );
    });
});
