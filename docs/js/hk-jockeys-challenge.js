document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.getElementById("challengeTable");

  fetch("data/hong-kong-jockeys-challenge.json")
    .then(res => {
      if (!res.ok) throw new Error("JSON not found");
      return res.json();
    })
    .then(data => {
      // Sort newest to oldest
      data.sort((a, b) => b.year - a.year);

      tableBody.innerHTML = "";

      data.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.year}</td>
          <td>${row.winner}</td>
        `;
        tableBody.appendChild(tr);
      });
    })
    .catch(err => {
      console.error(err);
      tableBody.innerHTML =
        `<tr><td colspan="2">Unable to load data.</td></tr>`;
    });
});
