document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ Breeders Cup JS running");

  const tbody = document.getElementById("results-body");

  fetch("docs/breeders-cup-results.json", { cache: "no-store" })
    .then(r => {
      console.log("Fetch status:", r.status);
      return r.json();
    })
    .then(data => {
      console.log("Rows loaded:", data.length);

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
    .catch(err => {
      console.error("❌ Fetch failed", err);
      tbody.innerHTML =
        `<tr><td colspan="6">Failed to load data</td></tr>`;
    });
});
