// Function to dynamically set the current year in the footer
document.addEventListener("DOMContentLoaded", function () {
  const currentYearElement = document.getElementById("current-year");
  if (currentYearElement) {
    currentYearElement.textContent = new Date().getFullYear();
  }
});

// Autocomplete Suggestions
document
  .getElementById("movie-title")
  .addEventListener("input", async function () {
    const query = this.value.trim();
    if (!query) {
      document.getElementById("movie-suggestions").innerHTML = "";
      return;
    }

    try {
      const response = await fetch(`/suggest?q=${encodeURIComponent(query)}`);
      const suggestions = await response.json();

      const datalist = document.getElementById("movie-suggestions");
      datalist.innerHTML = ""; // Clear previous suggestions
      suggestions.forEach((title) => {
        const option = document.createElement("option");
        option.value = title;
        datalist.appendChild(option);
      });
    } catch (error) {
      console.error("Error fetching suggestions:", error);
    }
  });

// Search Form Submission
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
    const movieDetailsDiv = document.getElementById("movie-details");
    const loader = document.querySelector(".loader");

    // Clear previous results and movie details
    resultsDiv.innerHTML = "";
    movieDetailsDiv.innerHTML = "";
    loader.style.display = "block"; // Show loader

    try {
      const response = await fetch("/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `movie_title=${encodeURIComponent(movieTitle)}`,
      });

      const data = await response.json();
      loader.style.display = "none"; // Hide loader

      if (data.error) {
        resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
        return;
      }

      // Display movie details if available
      const movieDetails = data.movie_details;
      if (movieDetails && Object.keys(movieDetails).length > 0) {
        movieDetailsDiv.innerHTML = `
              <div class="movie-info">
                  <h3>Film Details</h3>
                  <p><strong>Title:</strong> ${movieDetails.Title || "N/A"}</p>
                  <p><strong>Released:</strong> ${
                    movieDetails.Released || "N/A"
                  }</p>
                  <p><strong>Runtime:</strong> ${
                    movieDetails.Runtime || "N/A"
                  }</p>
                  <p><strong>Genre:</strong> ${movieDetails.Genre || "N/A"}</p>
                  <p><strong>Director:</strong> ${
                    movieDetails.Director || "N/A"
                  }</p>
                  <p><strong>Plot:</strong> ${movieDetails.Plot || "N/A"}</p>
                  <p><strong>IMDb Rating:</strong> ${
                    movieDetails.Ratings || "N/A"
                  }</p>
              </div>
          `;
      } else {
        movieDetailsDiv.innerHTML = `<p>No movie details found.</p>`;
      }

      // Display results in tables
      displayResults(data.movies, "Movies", resultsDiv);
      displayResults(data.subtitles, "Subtitles", resultsDiv);
    } catch (error) {
      loader.style.display = "none"; // Hide loader
      resultsDiv.innerHTML = `<p class="error">An error occurred while fetching results.</p>`;
    }
  });

// Function to display results in tables
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
              <td><span class="clickable-link" onclick="window.open('${link}', '_blank')">${link}</span></td>
              <td class="${statusClass}">${status}</td>
          </tr>
      `;
  }

  container.appendChild(table);
}
