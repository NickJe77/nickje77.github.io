const DATA_URL = "/data/australia-stakes.json";

fetch(DATA_URL)
  .then(res => res.json())
  .then(data => renderTable(data))
  .catch(err => console.error("JSON load failed:", err));

function cleanNumber(val) {
  if (!val) return "";
  return parseFloat(String(val).replace(/[^0-9.]/g, ""));
}

function renderTable(rows) {

  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";

  let rendered = 0;

  rows.forEach((r, i) => {
    try {

      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${r.date || ""}</td>
        <td>${r.track || ""}</td>
        <td>${r.grade || ""}</td>
        <td>${r.distance || ""}</td>
        <td>${r.winner || ""}</td>
        <td>${cleanNumber(r.margin)}</td>
        <td>${cleanNumber(r.sp)}</td>
        <td>${r["race grade"] || ""}</td>
        <td>${r.jockey || ""}</td>
        <td>${r.trainer || ""}</td>
      `;

      tbody.appendChild(tr);
      rendered++;

    } catch (e) {
      console.warn("Skipped bad row:", i, r);
    }
  });

  console.log("Australia Stakes rows rendered:", rendered);
}
