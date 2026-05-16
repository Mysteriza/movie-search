(() => {
  // --- Initialization ---
  document.addEventListener("DOMContentLoaded", () => {
    const currentYearElement = document.getElementById("current-year");
    if (currentYearElement) {
      currentYearElement.textContent = new Date().getFullYear();
    }
    
    // Fetch trending on load
    fetchTrendingMovies();
  });

  // --- State & DOM Elements ---
  const movieTitleInput = document.getElementById("movie-title");
  const autocompleteDropdown = document.getElementById("autocomplete-dropdown");
  const searchForm = document.getElementById("search-form");
  const searchBtn = document.getElementById("search-btn");
  const resultsDiv = document.getElementById("results");
  const movieDetailsDiv = document.getElementById("movie-details");
  const loader = document.getElementById("main-loader");
  const welcomeContent = document.getElementById("welcome-content");
  const statusMessage = document.getElementById("status-message");
  
  const trendingSection = document.getElementById("trending-movies-section");
  const trendingList = document.getElementById("trending-movies-list");

  let selectedIndex = -1;
  let currentSuggestions = [];
  let isSearching = false;

  // --- Utility Functions ---
  const debounce = (func, delay) => {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => func.apply(this, args), delay);
    };
  };

  // --- Trending Movies Feature ---
  async function fetchTrendingMovies() {
    try {
      const response = await fetch('/api/trending');
      const movies = await response.json();
      
      if (movies && movies.length > 0) {
        renderTrendingMovies(movies);
        trendingSection.style.display = 'block';
      }
    } catch (error) {
      console.error("Error fetching trending movies:", error);
    }
  }

  function renderTrendingMovies(movies) {
    trendingList.innerHTML = movies.map(movie => `
      <div class="trending-card" data-title="${movie.title}" data-year="${movie.year}">
        <div class="poster-wrapper">
          <img src="${movie.poster}" alt="${movie.title}" loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'150\\' height=\\'225\\' viewBox=\\'0 0 150 225\\'%3E%3Crect fill=\\'%23333\\' width=\\'150\\' height=\\'225\\'/%3E%3Ctext x=\\'75\\' y=\\'112\\' text-anchor=\\'middle\\' fill=\\'%23666\\' font-size=\\'24\\'%3E🎬%3C/text%3E%3C/svg%3E'">
        </div>
        <div class="trending-info">
          <div class="trending-title" title="${movie.title}">${movie.title}</div>
          <div class="trending-year">${movie.year}</div>
        </div>
      </div>
    `).join('');

    // Wire up clicks
    const cards = trendingList.querySelectorAll('.trending-card');
    cards.forEach(card => {
      card.addEventListener('click', () => {
        const title = card.getAttribute('data-title');
        const year = card.getAttribute('data-year');
        
        movieTitleInput.value = `${title} (${year})`;
        autocompleteDropdown.classList.remove('show');
        
        // Trigger submit
        searchForm.dispatchEvent(new Event("submit"));
      });
    });
  }

  // --- Autocomplete Feature ---
  function setDropdownExpanded(expanded) {
    movieTitleInput.setAttribute("aria-expanded", String(expanded));
  }

  function renderDropdown(suggestions) {
    currentSuggestions = suggestions;
    selectedIndex = -1;

    if (suggestions.length === 0) {
      autocompleteDropdown.classList.remove("show");
      autocompleteDropdown.innerHTML = "";
      setDropdownExpanded(false);
      return;
    }

    autocompleteDropdown.innerHTML = suggestions
      .map((item, index) => {
        const posterSrc = item.poster && item.poster !== "N/A"
            ? item.poster
            : "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='60' viewBox='0 0 40 60'%3E%3Crect fill='%23333' width='40' height='60'/%3E%3Ctext x='20' y='35' text-anchor='middle' fill='%23666' font-size='24'%3E🎬%3C/text%3E%3C/svg%3E";
        return `
        <div class="autocomplete-item" data-index="${index}" role="option" aria-selected="false">
          <img src="${posterSrc}" alt="${item.title}" class="autocomplete-poster" loading="lazy" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'40\\' height=\\'60\\' viewBox=\\'0 0 40 60\\'%3E%3Crect fill=\\'%23333\\' width=\\'40\\' height=\\'60\\'/%3E%3Ctext x=\\'20\\' y=\\'35\\' text-anchor=\\'middle\\' fill=\\'%23666\\' font-size=\\'24\\'%3E🎬%3C/text%3E%3C/svg%3E'">
          <div class="autocomplete-info">
            <span class="autocomplete-title">${item.title}</span>
            <span class="autocomplete-year">${item.year}</span>
          </div>
        </div>
      `;
      }).join("");

    autocompleteDropdown.classList.add("show");
    setDropdownExpanded(true);
  }

  function selectItem(index) {
    if (index >= 0 && index < currentSuggestions.length) {
      const item = currentSuggestions[index];
      movieTitleInput.value = `${item.title} (${item.year})`;
      autocompleteDropdown.classList.remove("show");
      autocompleteDropdown.innerHTML = "";
      currentSuggestions = [];
      selectedIndex = -1;
      searchForm.dispatchEvent(new Event("submit"));
    }
  }

  function updateActiveItem() {
    const items = autocompleteDropdown.querySelectorAll(".autocomplete-item");
    items.forEach((item, index) => {
      if (index === selectedIndex) {
        item.classList.add("active");
        item.setAttribute("aria-selected", "true");
        item.scrollIntoView({ block: "nearest" });
      } else {
        item.classList.remove("active");
        item.setAttribute("aria-selected", "false");
      }
    });
  }

  const fetchSuggestions = debounce(async function () {
    const query = movieTitleInput.value.trim();
    if (!query || query.length < 2) {
      autocompleteDropdown.classList.remove("show");
      autocompleteDropdown.innerHTML = "";
      return;
    }

    try {
      const response = await fetch(`/suggest?q=${encodeURIComponent(query)}`);
      const suggestions = await response.json();
      renderDropdown(suggestions);
    } catch (error) {
      console.error("Error fetching suggestions:", error);
    }
  }, 300);

  // --- Search Feature ---
  function displayMovieDetails(movieDetails) {
    if (movieDetails && Object.keys(movieDetails).length > 0) {
      const posterSrc = movieDetails.Poster && movieDetails.Poster !== "N/A" ? movieDetails.Poster : null;
      const posterHtml = posterSrc
        ? `<div class="movie-poster-container">
             <img src="${posterSrc}" alt="${movieDetails.Title}" class="movie-poster" loading="lazy">
           </div>`
        : "";

      movieDetailsDiv.innerHTML = `
        <h3>Film Details</h3>
        <div class="movie-details-layout">
          ${posterHtml}
          <div class="movie-info-container">
            <table class="movie-info-table">
              <tbody>
                <tr><th>Title:</th><td>${movieDetails.Title || "N/A"}</td></tr>
                <tr><th>Released:</th><td>${movieDetails.Released || "N/A"}</td></tr>
                <tr><th>Runtime:</th><td>${movieDetails.Runtime || "N/A"}</td></tr>
                <tr><th>Genre:</th><td>${movieDetails.Genre || "N/A"}</td></tr>
                <tr><th>Director:</th><td>${movieDetails.Director || "N/A"}</td></tr>
                <tr><th>Plot:</th><td>${movieDetails.Plot || "N/A"}</td></tr>
                <tr><th>IMDb Rating:</th><td>${movieDetails.Ratings || "N/A"}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    } else {
      movieDetailsDiv.innerHTML = `<p>No movie details found.</p>`;
    }
  }

  function getCategoryIcon(title) {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes("download")) return "⬇️";
    if (lowerTitle.includes("streaming")) return "📺";
    if (lowerTitle.includes("torrent")) return "🧲";
    if (lowerTitle.includes("subtitle")) return "📝";
    return "🎬";
  }

  function displayResults(links, title, container) {
    if (!links || links.length === 0) {
      container.innerHTML += `<p>No results found for ${title.toLowerCase()}.</p>`;
      return;
    }

    const sectionDiv = document.createElement("div");
    sectionDiv.className = "results-section";

    const heading = document.createElement("h3");
    heading.innerHTML = `${getCategoryIcon(title)} ${title}`;
    sectionDiv.appendChild(heading);

    let tbodyHtml = '';
    links.forEach((item, index) => {
      tbodyHtml += `
        <tr>
          <td>${index + 1}</td>
          <td>${item.name}</td>
          <td><button class="visit-btn" onclick="window.open('${item.url}', '_blank')">Visit</button></td>
        </tr>
      `;
    });

    const table = document.createElement("table");
    table.innerHTML = `
      <thead>
        <tr>
          <th style="width: 60px;">#</th>
          <th>Website</th>
          <th style="width: 120px;">Action</th>
        </tr>
      </thead>
      <tbody>${tbodyHtml}</tbody>
    `;

    sectionDiv.appendChild(table);
    container.appendChild(sectionDiv);
  }

  // --- Event Listeners ---
  movieTitleInput.addEventListener("input", fetchSuggestions);

  movieTitleInput.addEventListener("keydown", (e) => {
    if (!autocompleteDropdown.classList.contains("show")) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
      updateActiveItem();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      updateActiveItem();
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      selectItem(selectedIndex);
    } else if (e.key === "Escape") {
      autocompleteDropdown.classList.remove("show");
      selectedIndex = -1;
    }
  });

  autocompleteDropdown.addEventListener("click", (e) => {
    const item = e.target.closest(".autocomplete-item");
    if (item) {
      const index = parseInt(item.dataset.index, 10);
      selectItem(index);
    }
  });

  document.addEventListener("click", (e) => {
    if (!movieTitleInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
      autocompleteDropdown.classList.remove("show");
    }
  });

  function setStatusMessage(msg) {
    if (statusMessage) statusMessage.textContent = msg;
  }

  searchForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (isSearching) return;
    autocompleteDropdown.classList.remove("show");
    setDropdownExpanded(false);

    let movieTitle = movieTitleInput.value.trim();
    if (!movieTitle) {
      setStatusMessage("Please enter a movie title.");
      movieTitleInput.focus();
      return;
    }

    let movieYear = "";
    const yearMatch = movieTitle.match(/(.+?)\s*\((\d{4}).*\)$/);
    if (yearMatch) {
      movieTitle = yearMatch[1].trim();
      movieYear = yearMatch[2];
    }

    if (welcomeContent) welcomeContent.style.display = "none";
    if (trendingSection) trendingSection.style.display = "none";

    resultsDiv.innerHTML = "";
    movieDetailsDiv.innerHTML = "";
    loader.style.display = "block";
    searchBtn.disabled = true;
    searchBtn.textContent = "Searching...";
    isSearching = true;
    setStatusMessage(`Searching for ${movieTitle}...`);

    try {
      const response = await fetch("/search", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `movie_title=${encodeURIComponent(movieTitle)}&movie_year=${encodeURIComponent(movieYear)}`,
      });

      const data = await response.json();

      if (response.status === 429) {
        resultsDiv.innerHTML = `<p class="error" role="alert">Rate limit exceeded. Please try again later.</p>`;
        setStatusMessage("Rate limit exceeded. Please try again later.");
        return;
      }
      if (data.error) {
        resultsDiv.innerHTML = `<p class="error" role="alert">${data.error}</p>`;
        setStatusMessage(`Search failed: ${data.error}`);
        return;
      }

      displayMovieDetails(data.movie_details);

      displayResults(data.downloads, "Movies & TV Show - Download Only", resultsDiv);
      displayResults(data.tvshow_downloads, "TV Show - Download Only", resultsDiv);
      displayResults(data.streaming, "Movies & TV Show - Streaming Only", resultsDiv);
      displayResults(data.tvshows, "TV Show - Streaming Only", resultsDiv);
      displayResults(data.torrents, "Torrents", resultsDiv);
      displayResults(data.subtitles, "Subtitles", resultsDiv);

      setStatusMessage(`Found results for ${movieTitle}.`);
    } catch (error) {
      resultsDiv.innerHTML = `<p class="error" role="alert">An error occurred while fetching results. Please try again.</p>`;
      setStatusMessage("An error occurred while fetching results.");
    } finally {
      loader.style.display = "none";
      searchBtn.disabled = false;
      searchBtn.textContent = "Search";
      isSearching = false;
    }
  });

})();
