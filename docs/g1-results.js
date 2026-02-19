// g1-results.js (robust + safe + includes counter)

document.addEventListener("DOMContentLoaded", () => {
  const yearFilter = document.getElementById("yearFilter");
  const raceFilter = document.getElementById("raceFilter");
  const winnerFilter = document.getElementById("winnerFilter");
  const jockeyFilter = document.getElementById("jockeyFilter");
  const countryFilter = document.getElementById("countryFilter");

  const raceList = document.getElementById("raceList");
  const winnerList = document.getElementById("winnerList");
  const jockeyList = document.getElementById("jockeyList");
  const countryList = document.getElementById("countryList");

  const tableBody = document.querySelector("tbody");
  const resultCounter = document.getElementById("resultCounter");

  let allData = [];

  const pick = (obj, keys) => {
    for (const k of keys) {
      if (obj && obj[k] !== undefined && obj[k] !== null && String(obj[k]).trim() !== "") return obj[k];
    }
    return "";
  };

  const norm = (row) => {
    // supports UPPERCASE and lowercase
    const YEAR = pick(row, ["YEAR", "year", "Year"]);
    const RACE = pick(row, ["RACE", "race", "Race"]);
    const TRACK = pick(row, ["TRACK", "track", "Track"]);
    const WINNER = pick(row, ["WINNER", "winner", "Winner"]);
    const TRAINER = pick(row, ["TRAINER", "trainer", "Trainer"]);
    const JOCKEY = pick(row, ["JOCKEY", "jockey", "Jockey"]);
    const COUNTRY = pick(row, ["COUNTRY", "country", "Country"]);

    return {
      YEAR: YEAR === "" ? "" : Number(YEAR),
      RACE: String(RACE || ""),
      TRACK: String(TRACK || ""),
      WINNER: String(WINNER || ""),
      TRAINER: String(TRAINER || ""),
      JOCKEY: String(JOCKEY || ""),
      COUNTRY: String(COUNTRY || "")
    };
  };

  const safeLower = (v) => String(v || "").toLowerCase();

  const uniq = (arr) => [...new Set(arr.filter(v => v !== "" && v !== null && v !== undefined))];

  const fillDatalist = (dl, values) => {
    dl.innerHTML = "";
    values.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v;
      dl.appendChild(opt);
    });
  };

  const updateCounter = (n) => {
    resultCounter.textContent = `Showing ${n} result${n === 1 ? "" : "s"}`;
  };

  const renderTable = (rows) => {
    tableBody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.YEAR || ""}</td>
        <td>${r.RACE || ""}</td>
        <td>${r.TRACK || ""}</td>
        <td>${r.WINNER || ""}</td>
        <td>${r.TRAINER || ""}</td>
        <td>${r.JOCKEY || ""}</td>
        <td>${r.COUNTRY || ""}</td>
      </tr>
    `).join("");
  };

  const populateFilters = () => {
    const years = uniq(allData.map(d => d.YEAR)).sort((a, b) => b - a);
    yearFilter.innerHTML = `<option value="">All</option>` + years.map(y => `<option value="${y}">${y}</option>`).join("");

    fillDatalist(raceList, uniq(allData.map(d => d.RACE)).sort());
    fillDatalist(winnerList, uniq(allData.map(d => d.WINNER)).sort());
    fillDatalist(jockeyList, uniq(allData.map(d => d.JOCKEY)).sort());
    fillDatalist(countryList, uniq(allData.map(d => d.COUNTRY)).sort());
  };

  const applyFilters = () => {
    const yearVal = yearFilter.value;
    const raceVal = safeLower(raceFilter.value).trim();
    const winnerVal = safeLower(winnerFilter.value).trim();
    const jockeyVal = safeLower(jockeyFilter.value).trim();
    const countryVal = safeLower(countryFilter.value).trim();

    const filtered = allData.filter(r =>
      (!yearVal || String(r.YEAR) === String(yearVal)) &&
      (!raceVal || safeLower(r.RACE).includes(raceVal)) &&
      (!winnerVal || safeLower(r.WINNER).includes(winnerVal)) &&
      (!jockeyVal || safeLower(r.JOCKEY).includes(jockeyVal)) &&
      (!countryVal || safeLower(r.COUNTRY).includes(countryVal))
    );

    renderTable(filtered);
    updateCounter(filtered.length);
  };

  // IMPORTANT: JSON is in the SAME folder as this HTML/JS
  fetch("g1-results.json")
    .then(res => res.json())
    .then(json => {
      allData = (Array.isArray(json) ? json : [])
        .filter(x => x && typeof x === "object")
        .map(norm)
        .filter(r => r.YEAR !== "" || r.RACE || r.WINNER || r.JOCKEY || r.COUNTRY);

      allData.sort((a, b) => (b.YEAR || 0) - (a.YEAR || 0) || String(a.RACE).localeCompare(String(b.RACE)));

      populateFilters();
      applyFilters();
    })
    .catch(err => {
      console.error("Failed to load g1-results.json", err);
      tableBody.innerHTML = `<tr><td colspan="7">Failed to load data.</td></tr>`;
      updateCounter(0);
    });

  [yearFilter, raceFilter, winnerFilter, jockeyFilter, countryFilter].forEach(el => {
    el.addEventListener("input", applyFilters);
    el.addEventListener("change", applyFilters);
  });
});
