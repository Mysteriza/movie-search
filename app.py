import hashlib
import logging
import os
import secrets
import urllib.parse

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

from services.movie_service import get_all_movie_links
from utils.helpers import convert_runtime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

CORS(app, resources={r"/suggest": {"origins": "*"}, r"/search": {"origins": "*"}, r"/api/trending": {"origins": "*"}})
Compress(app)

flask_env = os.getenv("FLASK_ENV", "production")

logging.basicConfig(
    level=logging.INFO if flask_env == "production" else logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
)

cache = Cache(
    app,
    config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 3600,
    },
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

csp = {
    "default-src": "'self'",
    "script-src": "'self' 'unsafe-inline'",
    "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src": "'self' https://fonts.gstatic.com",
    "img-src": "'self' data: https:",
    "connect-src": "'self' https://www.omdbapi.com",
}

if flask_env != "development":
    Talisman(
        app,
        content_security_policy=csp,
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True,
    )


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy"}), 200


@app.route("/api/trending", methods=["GET"])
@cache.cached(timeout=3600)
def trending():
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    if not tmdb_api_key:
        app.logger.error("TMDB_API_KEY not found")
        return jsonify([])

    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={tmdb_api_key}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "results" in data:
            movies = []
            for item in data["results"][:15]:
                title = item.get("title")
                poster_path = item.get("poster_path")
                release_date = item.get("release_date", "")
                year = release_date.split("-")[0] if release_date else "N/A"
                if title and poster_path:
                    movies.append({
                        "title": title,
                        "year": year,
                        "poster": f"https://image.tmdb.org/t/p/w300{poster_path}"
                    })
            return jsonify(movies)
        else:
            app.logger.warning(f"TMDb error: {data}")
            return jsonify([])
    except Exception as e:
        app.logger.error(f"Error fetching trending: {e}")
        return jsonify([])


@app.route("/suggest", methods=["GET"])
@limiter.limit("30 per minute")
@cache.cached(timeout=300, query_string=True)
def suggest():
    query = request.args.get("q", "").strip()

    if not query or len(query) > 100:
        return jsonify([])

    if not all(c.isalnum() or c.isspace() or c in "'-:.,!?" for c in query):
        return jsonify([])

    omdb_api_key = os.getenv("OMDB_API_KEY")
    if not omdb_api_key:
        app.logger.error("OMDB_API_KEY not found")
        return jsonify([])

    url = f"https://www.omdbapi.com/?s={query}&apikey={omdb_api_key}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        app.logger.info(f"OMDb Response for '{query}': {data.get('Response')}")
        if data.get("Response") == "True":
            suggestions = [
                {
                    "title": movie.get("Title", "Unknown"),
                    "year": movie.get("Year", "N/A"),
                    "poster": movie.get("Poster", "N/A"),
                }
                for movie in data.get("Search", [])
            ]
            return jsonify(suggestions[:10])
        else:
            app.logger.warning(f"OMDb returned False for query: {query}, Error: {data.get('Error')}")
            return jsonify([])
    except Exception as e:
        app.logger.error(f"Error fetching suggestions: {e}")
        return jsonify([])


@app.route("/search", methods=["POST"])
@limiter.limit("10 per minute")
def search():
    movie_title = request.form.get("movie_title", "").strip()
    movie_year = request.form.get("movie_year", "").strip()

    if not movie_title:
        return jsonify({"error": "Please enter a movie title."}), 400
    if len(movie_title) > 100:
        return jsonify({"error": "Movie title too long."}), 400
    if movie_year and not movie_year.isdigit():
        return jsonify({"error": "Invalid year format."}), 400
    if not all(c.isalnum() or c.isspace() or c in "'-:.,!?" for c in movie_title):
        return jsonify({"error": "Invalid characters in movie title."}), 400

    cache_key = f"search_result:{hashlib.md5(f'{movie_title}|{movie_year}'.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is not None:
        app.logger.info(f"Cache hit for: {movie_title} ({movie_year})")
        return jsonify(cached)

    movie_details = {}
    omdb_api_key = os.getenv("OMDB_API_KEY")
    
    if omdb_api_key:
        omdb_url = f"https://www.omdbapi.com/?t={urllib.parse.quote_plus(movie_title)}&apikey={omdb_api_key}"
        if movie_year:
            omdb_url += f"&y={movie_year}"
        try:
            omdb_response = requests.get(omdb_url, timeout=5)
            omdb_data = omdb_response.json()
            if omdb_data.get("Response") == "True":
                runtime = omdb_data.get("Runtime", "N/A")
                movie_details = {
                    "Title": omdb_data.get("Title"),
                    "Released": omdb_data.get("Released"),
                    "Runtime": convert_runtime(runtime),
                    "Genre": omdb_data.get("Genre"),
                    "Director": omdb_data.get("Director"),
                    "Plot": omdb_data.get("Plot"),
                    "Poster": omdb_data.get("Poster", "N/A"),
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

    links_dict = get_all_movie_links(movie_title)
    
    result = {"movie_details": movie_details, **links_dict}
    cache.set(cache_key, result, timeout=259200)
    app.logger.info(f"Cached result for: {movie_title} ({movie_year})")
    
    return jsonify(result)


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV", "production") == "development"
    app.run(debug=debug_mode)
