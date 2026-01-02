document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ script.js loaded");

  const tableBody = document.querySelector("#racingTable tbody");
  if (!tableBody) {
    console.log("ℹ️ Not on racing page");
    return;
  }

  fetch("/data/g1-racing.json")
    .then(response => {
      if (!response.ok) {
        throw new Error("HTTP error " + response.status);
      }
      return response.json();
    })
    .then(data => {
      console.log("✅ Racing data loaded", data);

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
      console.error("❌ Racing data load failed", err);
    });
});
