document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("results-body");

  fetch("breeders-cup-results.json", { cache: "no-store" })
    .then(res => res.json())
    .then(data => {
      tbody.innerHTML = "";

      data.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.year}</td>
          <td>${row.race}</td>
          <td>${row.track}</td>
          <td>${row.winner}</td>
          <td>${row.jockey}</td>
          <td>${row.trainer}</td>
        `;
        tbody.appendChild(tr);
      });
    })
    .catch(() => {
      tbody.innerHTML =
        `<tr><td colspan="6">Unable to load results</td></tr>`;
    });
});
