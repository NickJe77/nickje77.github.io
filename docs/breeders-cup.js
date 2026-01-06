document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ Breeders Cup JS loaded");

  const tbody = document.getElementById("results-body");

  if (!tbody) {
    console.error("❌ results-body not found");
    return;
  }

  fetch("breeders-cup-results.json", { cache: "no-store" })
    .then(r => {
      console.log("📡 Fetch status:", r.status);
      return r.json();
    })
    .then(data => {
      console.log("📦 Rows in JSON:", data.length);

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

      console.log("✅ Rows rendered");
    })
    .catch(err => {
      console.error("🔥 FETCH FAILED", err);
      tbody.innerHTML =
        `<tr><td colspan="6">Fetch failed – check console</td></tr>`;
    });
});
