console.log("🔥 JS FILE EXECUTED");

fetch("/breeders-cup-results.json", { cache: "no-store" })
  .then(r => r.json())
  .then(data => {
    console.log("📦 JSON rows:", data.length);

    const tbody = document.getElementById("results-body");
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
  .catch(err => console.error("❌ FAILED", err));
