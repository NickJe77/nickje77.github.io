document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.querySelector("#racingTable tbody");
  if (!tableBody) {
    console.error("❌ Table body not found");
    return;
  }

  fetch("./data/g1-racing.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON fetch failed");
      return res.json();
    })
    .then(data => {
      console.log("✅ Racing data:", data);

      tableBody.innerHTML = "";

      data.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.year}</td>
          <td>${row.race}</td>
          <td>${row.country}</td>
          <td>${row.track}</td>
          <td>${row.winner}</td>
          <td>${row.jockey}</td>
          <td>${row.trainer}</td>
        `;
        tableBody.appendChild(tr);
      });
    })
    .catch(err => {
      console.error("❌ Fatal error:", err);
    });
});

