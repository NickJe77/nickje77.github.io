fetch('g1-results.json')
  .then(response => response.json())
  .then(data => {
    const tbody = document.getElementById('results-body');

    data
      .sort((a, b) => b.year - a.year)
      .forEach(row => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
          <td>${row.year}</td>
          <td>${row.race}</td>
          <td>${row.track}</td>
          <td>${row.winner}</td>
          <td>${row.jockey}</td>
          <td>${row.trainer}</td>
          <td>${row.country}</td>
        `;

        tbody.appendChild(tr);
      });
  });

