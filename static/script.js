// Function to dynamically set the current year in the footer
document.addEventListener("DOMContentLoaded", function () {
  const currentYearElement = document.getElementById("current-year");
  if (currentYearElement) {
    currentYearElement.textContent = new Date().getFullYear();
  }
});

// Debounce function to limit API calls
function debounce(func, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => func.apply(this, args), delay);
  };
}

// Autocomplete Suggestions with Responsiveness and Precision
const movieTitleInput = document.getElementById("movie-title");
const movieSuggestions = document.getElementById("movie-suggestions");

let isSuggestionSelected = false; // Track if a suggestion is selected

// Debounced function for fetching suggestions
const fetchSuggestions = debounce(async function () {
  const query = movieTitleInput.value.trim();
  if (!query || isSuggestionSelected) {
    movieSuggestions.innerHTML = "";
    return;
  }

  try {
    const response = await fetch(`/suggest?q=${encodeURIComponent(query)}`);
    const suggestions = await response.json();

    movieSuggestions.innerHTML = ""; // Clear previous suggestions
    suggestions.forEach((title) => {
      const option = document.createElement("option");
      option.value = title;
      movieSuggestions.appendChild(option);
    });
  } catch (error) {
    console.error("Error fetching suggestions:", error);
  }
}, 300); // Delay of 300ms to debounce API calls

// Attach input event listener for responsiveness
movieTitleInput.addEventListener("input", () => {
  isSuggestionSelected = false; // Reset flag when user starts typing again
  fetchSuggestions();
});

// Handle selection from suggestions
movieTitleInput.addEventListener("change", () => {
  isSuggestionSelected = true; // Mark suggestion as selected
  movieSuggestions.innerHTML = ""; // Clear suggestions after selection
});

// Display movie details in a table format
function displayMovieDetails(movieDetails) {
  const movieDetailsDiv = document.getElementById("movie-details");

  if (movieDetails && Object.keys(movieDetails).length > 0) {
    const table = document.createElement("table");
    table.classList.add("movie-info-table");

    // Populate the table with movie details
    table.innerHTML = `
          <tr>
              <th>Title:</th>
              <td>${movieDetails.Title || "N/A"}</td>
          </tr>
          <tr>
              <th>Released:</th>
              <td>${movieDetails.Released || "N/A"}</td>
          </tr>
          <tr>
              <th>Runtime:</th>
              <td>${movieDetails.Runtime || "N/A"}</td>
          </tr>
          <tr>
              <th>Genre:</th>
              <td>${movieDetails.Genre || "N/A"}</td>
          </tr>
          <tr>
              <th>Director:</th>
              <td>${movieDetails.Director || "N/A"}</td>
          </tr>
          <tr>
              <th>Plot:</th>
              <td>${movieDetails.Plot || "N/A"}</td>
          </tr>
          <tr>
              <th>IMDb Rating:</th>
              <td>${movieDetails.Ratings || "N/A"}</td>
          </tr>
      `;

    movieDetailsDiv.innerHTML = `<h3>Film Details</h3>`;
    movieDetailsDiv.appendChild(table);
  } else {
    movieDetailsDiv.innerHTML = `<p>No movie details found.</p>`;
  }
}

// Search Form Submission
document
  .getElementById("search-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    const movieTitle = movieTitleInput.value.trim();
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

      if (response.status === 429) {
        resultsDiv.innerHTML = `<p class="error">Rate limit exceeded. Please try again later.</p>`;
        return;
      }

      if (data.error) {
        resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
        return;
      }

      // Display movie details in a table format
      displayMovieDetails(data.movie_details);

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
