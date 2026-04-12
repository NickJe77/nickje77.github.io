<script>

// GET YEAR
const params = new URLSearchParams(window.location.search);
const year = parseInt(params.get("year"));

// LOAD DATA
fetch(`/data/bathurst/${year}.json`)
  .then(res => res.json())
  .then(data => {

    if(!data || !data.results){
      document.getElementById("title").textContent = "Race not found";
      return;
    }

    document.getElementById("title").textContent =
      `${year} Bathurst 1000`;

    const table = document.getElementById("results");
    table.innerHTML = "";

    data.results
      .sort((a,b) => a.finish - b.finish)
      .forEach(r => {

        const tr = document.createElement("tr");

        // POSITION
        const tdPos = document.createElement("td");
        tdPos.textContent = r.finish || "";

        // DRIVERS (SAFE)
        const tdDrivers = document.createElement("td");

        (r.drivers || []).forEach((d, i) => {
          const a = document.createElement("a");
          a.className = "driver";
          a.href = `./bathurst-driver.html?driver=${d.toLowerCase().replace(/ /g, "-")}`;
          a.textContent = d;

          tdDrivers.appendChild(a);

          if(i < r.drivers.length - 1){
            tdDrivers.appendChild(document.createTextNode(" / "));
          }
        });

        // CAR (SAFE)
        const tdCar = document.createElement("td");
        tdCar.textContent = r.car || "";

        tr.appendChild(tdPos);
        tr.appendChild(tdDrivers);
        tr.appendChild(tdCar);

        table.appendChild(tr);
      });

  })
  .catch(err => {
    document.getElementById("title").textContent = "Error loading race";
    console.error(err);
  });

</script>
