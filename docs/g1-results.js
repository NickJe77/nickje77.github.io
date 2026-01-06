document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector(".archive-table tbody");

  if (!tbody) {
    console.error("G1 Archive: <tbody> not found");
    return;
  }

  fetch("g1-results.json")
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      if (!Array.isArray(data)) {
        console.error("G1 Archive: data is not an array", data);
        return;
      }

      tbody.innerHTML = "";

      data.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.year ?? ""}</td>
          <td>${row.race ?? ""}</td>
          <td>${row.track ?? ""}</td>
          <td>${row.winner ?? ""}</td>
          <td>${row.country ?? ""}</td>
          <td>${row.trainer ?? ""}</td>
          <td>${row.jockey ?? ""}</td>
        `;
        tbody.appendChild(tr);
      });

      console.log(`G1 Archive loaded: ${data.length} rows`);
    })
    .catch(err => {
      console.error("G1 Archive failed to load data", err);
    });
});
