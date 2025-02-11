// Function to dynamically set the current year in the footer
document.addEventListener("DOMContentLoaded", function () {
  const currentYearElement = document.getElementById("current-year");
  if (currentYearElement) {
    currentYearElement.textContent = new Date().getFullYear();
  }
});

document
  .getElementById("search-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    const movieTitle = document.getElementById("movie-title").value.trim();
    if (!movieTitle) {
      alert("Please enter a movie title.");
      return;
    }

    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "<p id='loading'>Checking links... Please wait.</p>";

    try {
      const response = await fetch("/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `movie_title=${encodeURIComponent(movieTitle)}`,
      });

      const data = await response.json();
      if (data.error) {
        resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
        return;
      }

      // Remove loading message
      document.getElementById("loading").remove();

      // Display results in tables
      resultsDiv.innerHTML = "";
      displayResults(data.movies, "Movies", resultsDiv);
      displayResults(data.subtitles, "Subtitles", resultsDiv);

      // Add "Open All" button
      const openAllBtn = document.createElement("button");
      openAllBtn.className = "open-all-btn";
      openAllBtn.textContent = "Open All Links";
      openAllBtn.onclick = () => {
        const allLinks = [
          ...Object.keys(data.movies),
          ...Object.keys(data.subtitles),
        ];
        let delay = 0; // Delay in milliseconds
        allLinks.forEach((link, index) => {
          setTimeout(() => {
            window.open(link, "_blank");
          }, delay);
          delay += 500; // Add 500ms delay between each link
        });
      };
      resultsDiv.appendChild(openAllBtn);
    } catch (error) {
      resultsDiv.innerHTML = `<p class="error">An error occurred while fetching results.</p>`;
    }
  });

function displayResults(links, title, container) {
  if (Object.keys(links).length === 0) {
    container.innerHTML += `<p>No results found for ${title.toLowerCase()}.</p>`;
    return;
  }

  container.innerHTML += `<h3>${title}</h3>`;
  const table = document.createElement("table");
  table.innerHTML = `
        <thead>
            <tr>
                <th>Link</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;

  const tbody = table.querySelector("tbody");
  for (const [link, status] of Object.entries(links)) {
    const statusClass = status === "Found" ? "found" : "unsure"; // Only Found or Unsure
    tbody.innerHTML += `
            <tr>
                <td><a href="${link}" target="_blank">${link}</a></td>
                <td class="${statusClass}">${status}</td>
            </tr>
        `;
  }

  container.appendChild(table);
}
