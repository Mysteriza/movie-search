from flask import Flask, render_template, request, jsonify
import json
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)


# Load templates from JSON file
def load_templates():
    try:
        with open("templates.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"movie_templates": [], "subtitle_templates": []}


# Generate links based on templates using the original input
def generate_links(movie_title, templates):
    encoded_title = urllib.parse.quote_plus(movie_title)  # Encode special characters
    return [template.format(encoded_title) for template in templates]


# Check the status of a single link
def check_link(link):
    """
    Check the status of a single link using a random user agent.
    :param link: Link to check.
    :return: Tuple of (link, status).
    """
    headers = {"User-Agent": "Mozilla/5.0"}  # Default user-agent
    try:
        response = requests.get(link, headers=headers, timeout=5)
        if response.status_code == 200:
            return link, "Found"
        else:
            return link, "Unsure"
    except requests.RequestException:
        return link, "Unsure"


# Check multiple links concurrently
def check_links(links):
    link_status = {}
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_link = {executor.submit(check_link, link): link for link in links}
        for future in as_completed(future_to_link):
            link, status = future.result()
            link_status[link] = status
    return link_status


# Home route
@app.route("/")
def index():
    return render_template("index.html")


# Suggest route (Autocomplete using OMDb API)
@app.route("/suggest", methods=["GET"])
def suggest():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    omdb_api_key = os.getenv("OMDB_API_KEY")
    if not omdb_api_key:
        return jsonify([])

    url = f"http://www.omdbapi.com/?s={query}&apikey={omdb_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("Response") == "True":
            suggestions = [movie["Title"] for movie in data.get("Search", [])]
            return jsonify(suggestions[:10])  # Limit to 10 suggestions
        else:
            return jsonify([])
    except Exception as e:
        print(f"Error fetching suggestions: {e}")
        return jsonify([])


# Search route
@app.route("/search", methods=["POST"])
def search():
    movie_title = request.form.get("movie_title")
    if not movie_title:
        return jsonify({"error": "Please enter a movie title."}), 400

    # Initialize movie_details as empty by default
    movie_details = {}

    # Fetch movie details from OMDb API using the original input
    omdb_api_key = os.getenv("OMDB_API_KEY")
    if omdb_api_key:
        omdb_url = f"http://www.omdbapi.com/?t={urllib.parse.quote_plus(movie_title)}&apikey={omdb_api_key}"
        try:
            omdb_response = requests.get(omdb_url)
            omdb_data = omdb_response.json()
            if omdb_data.get("Response") == "True":
                # Extract relevant movie details if found
                movie_details = {
                    "Title": omdb_data.get("Title"),
                    "Released": omdb_data.get("Released"),
                    "Runtime": omdb_data.get("Runtime"),
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
            print(f"Error fetching OMDb data: {e}")

    # Generate links based on templates using the original input
    templates = load_templates()
    movie_links = generate_links(movie_title, templates["movie_templates"])
    subtitle_links = generate_links(movie_title, templates["subtitle_templates"])

    # Check links concurrently
    movie_link_status = check_links(movie_links)
    subtitle_link_status = check_links(subtitle_links)

    return jsonify(
        {
            "movie_details": movie_details
            or {},  # Return empty object if no details found
            "movies": movie_link_status,
            "subtitles": subtitle_link_status,
        }
    )


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
