const DATA_URL = "/data/australia-stakes.json";

fetch(DATA_URL)
  .then(res => res.json())
  .then(data => {
    renderTable(data);
  })
  .catch(err => {
    console.error("JSON load failed:", err);
  });

function cleanNumber(val) {
  if (!val) return "";
  return parseFloat(String(val).replace(/[^0-9.]/g, ""));
}

function renderTable(rows) {
  const tbody = document.querySelector("#results-body");
  tbody.innerHTML = "";

  let count = 0;

  rows.forEach((r, i) => {
    try {

      const track = r.track || "";
      const date = r.date || "";
      const grade = r.grade || "";
      const distance = r.distance || "";
      const winner = r.winner || "";
      const margin = cleanNumber(r.margin);
      const sp = cleanNumber(r.sp);
      const raceGrade = r["race grade"] || "";
      const jockey = r.jockey || "";
      const trainer = r.trainer || "";

      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${date}</td>
        <td>${track}</td>
        <td>${grade}</td>
        <td>${distance}</td>
        <td>${winner}</td>
        <td>${margin}</td>
        <td>${sp}</td>
        <td>${raceGrade}</td>
        <td>${jockey}</td>
        <td>${trainer}</td>
      `;

      tbody.appendChild(tr);
      count++;

    } catch (e) {
      console.warn("Bad row skipped at index", i, r);
    }
  });

  console.log("Rendered rows:", count);
}
