document.addEventListener("DOMContentLoaded", () => {
  fetch("/data/g1-results.json")
    .then(res => res.json())
    .then(data => {
      console.log("G1 DATA LOADED:", data);

      const tbody = document.querySelector("#results-table tbody");
      tbody.innerHTML = "";

      data.forEach(race => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${race.year}</td>
          <td>${race.race}</td>
          <td>${race.country}</td>
          <td>${race.track}</td>
          <td>${race.winner}</td>
          <td>${race.jockey}</td>
          <td>${race.trainer}</td>
        `;
        tbody.appendChild(row);
      });
    })
    .catch(err => console.error("DATA LOAD ERROR:", err));
});
