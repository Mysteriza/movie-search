from flask import Flask, render_template, request, jsonify
import json
import urllib.parse
import requests
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_caching import Cache
from flask_cors import CORS
from flask_compress import Compress
import logging

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS (only for API endpoints)
CORS(app, resources={r"/suggest": {"origins": "*"}, r"/search": {"origins": "*"}})

# Initialize compression
Compress(app)

# Configure logging
if os.getenv("FLASK_ENV") == "production":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
    )
else:
    logging.basicConfig(level=logging.DEBUG)

# Initialize cache
cache = Cache(
    app,
    config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes cache
    },
)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Initialize Talisman for HTTPS enforcement (disable in development)
if os.getenv("FLASK_ENV") != "development":
    Talisman(app, content_security_policy=None)  # CSP handled manually below


# Security headers middleware
@app.after_request
def set_security_headers(response):
    """Add security headers to every response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://www.omdbapi.com"
    )
    return response


# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429


# Load templates from JSON file
def load_templates():
    try:
        with open("templates.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"movie_templates": [], "subtitle_templates": []}


# Generate links based on templates using the original input
def generate_links(movie_title, templates):
    cleaned_title = movie_title.replace("'", "").replace('"', "").replace("'", "")
    encoded_title = urllib.parse.quote(cleaned_title, safe="")
    return [template.format(encoded_title) for template in templates]


def extract_website_name(url):
    website_mapping = {
        "130.185.118.151": "Driverays",
        "batch.moe": "Batchindo",
        "hydrahd.me": "HydraHD",
        "moviepire.net": "Moviepire",
        "nunflix.li": "Nunflix",
        "pahe.ink": "Pahe",
        "seriesonlinehd.net": "Series Online HD",
        "todaytvseries1.com": "Today TV Series",
        "tv11.idlixku.com": "idlix",
        "tvshows.ac": "TV Shows",
        "uflix.cc": "uFlix",
        "pencurimovie.bond": "Pencurimovie",
        "subdl.com": "Subdl",
        "subsource.net": "Subsource",
    }

    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = domain.replace("www.", "")

    for key, value in website_mapping.items():
        if key in domain:
            return value

    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[0].capitalize()
    return domain.capitalize()


def prepare_link_data(links):
    result = []
    for link in links:
        website_name = extract_website_name(link)
        result.append({"name": website_name, "url": link})
    return result


# Home route
@app.route("/")
def index():
    return render_template("index.html")


# Health check endpoint for Koyeb
@app.route("/health")
def health():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy"}), 200


# Suggest route (Autocomplete using OMDb API)
@app.route("/suggest", methods=["GET"])
@limiter.limit("30 per minute")
def suggest():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    if len(query) > 100:
        return jsonify([])

    if not all(c.isalnum() or c.isspace() or c in "'-:.,!?" for c in query):
        return jsonify([])

    omdb_api_key = os.getenv("OMDB_API_KEY")
    if not omdb_api_key:
        app.logger.error("OMDB_API_KEY not found")
        return jsonify([])

    url = f"http://www.omdbapi.com/?s={query}&apikey={omdb_api_key}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        app.logger.info(f"OMDb Response for '{query}': {data.get('Response')}")
        if data.get("Response") == "True":
            suggestions = [movie["Title"] for movie in data.get("Search", [])]
            return jsonify(suggestions[:10])
        else:
            app.logger.warning(
                f"OMDb returned False for query: {query}, Error: {data.get('Error')}"
            )
            return jsonify([])
    except Exception as e:
        app.logger.error(f"Error fetching suggestions: {e}")
        return jsonify([])


# Helper function to convert runtime from minutes to hours and minutes
def convert_runtime(runtime):
    """
    Convert runtime from minutes to hours and minutes format.
    Example: "169 min" -> "169 min (2h 8m)"
    :param runtime: Runtime string from OMDB API (e.g., "169 min").
    :return: Converted runtime string (e.g., "169 min (2h 8m)").
    """
    try:
        # Extract the number of minutes from the runtime string
        minutes = int(runtime.split()[0])
        hours = minutes // 60  # Calculate hours
        remaining_minutes = minutes % 60  # Calculate remaining minutes
        return f"{minutes} min ({hours}h {remaining_minutes}m)"
    except (ValueError, AttributeError):
        return runtime  # Return original runtime if conversion fails


# Search route
@app.route("/search", methods=["POST"])
@limiter.limit("10 per minute")
def search():
    movie_title = request.form.get("movie_title", "").strip()

    # Input validation
    if not movie_title:
        return jsonify({"error": "Please enter a movie title."}), 400

    if len(movie_title) > 100:  # Prevent excessive input
        return jsonify({"error": "Movie title too long."}), 400

    # Sanitize input
    if not all(c.isalnum() or c.isspace() or c in "'-:.,!?" for c in movie_title):
        return jsonify({"error": "Invalid characters in movie title."}), 400

    # Initialize movie_details as empty by default
    movie_details = {}

    # Fetch movie details from OMDb API using the original input
    omdb_api_key = os.getenv("OMDB_API_KEY")
    if omdb_api_key:
        omdb_url = f"http://www.omdbapi.com/?t={urllib.parse.quote_plus(movie_title)}&apikey={omdb_api_key}"
        try:
            omdb_response = requests.get(omdb_url, timeout=5)
            omdb_data = omdb_response.json()
            if omdb_data.get("Response") == "True":
                # Extract relevant movie details if found
                runtime = omdb_data.get("Runtime", "N/A")
                converted_runtime = convert_runtime(runtime)  # Convert runtime

                movie_details = {
                    "Title": omdb_data.get("Title"),
                    "Released": omdb_data.get("Released"),
                    "Runtime": converted_runtime,  # Use converted runtime
                    "Genre": omdb_data.get("Genre"),
                    "Director": omdb_data.get("Director"),
                    "Plot": omdb_data.get("Plot"),
                    "Ratings": next(
                        (
                            rating["Value"]
                            for rating in omdb_data.get("Ratings", [])
                            if rating["Source"] == "Internet Movie Database"
                        ),
                        "N/A",
                    ),
                }
        except Exception as e:
            app.logger.error(f"Error fetching OMDb data: {e}")

    # Generate links based on templates using the original input
    templates = load_templates()
    movie_links = generate_links(movie_title, templates["movie_templates"])
    subtitle_links = generate_links(movie_title, templates["subtitle_templates"])

    movie_link_data = prepare_link_data(movie_links)
    subtitle_link_data = prepare_link_data(subtitle_links)

    return jsonify(
        {
            "movie_details": movie_details or {},
            "movies": movie_link_data,
            "subtitles": subtitle_link_data,
        }
    )


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
