from colorama import Fore, Style
from flask import Flask, render_template, request, jsonify
import json
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

app = Flask(__name__)


# Load templates from JSON file
def load_templates():
    try:
        with open("templates.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"movie_templates": [], "subtitle_templates": []}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    movie_title = request.form.get("movie_title")
    if not movie_title:
        return jsonify({"error": "Please enter a movie title."}), 400

    templates = load_templates()
    movie_links = generate_links(movie_title, templates["movie_templates"])
    subtitle_links = generate_links(movie_title, templates["subtitle_templates"])

    # Check links concurrently
    movie_link_status = check_links(movie_links)
    subtitle_link_status = check_links(subtitle_links)

    return jsonify({"movies": movie_link_status, "subtitles": subtitle_link_status})


def generate_links(movie_title, templates):
    encoded_title = urllib.parse.quote_plus(movie_title)
    return [template.format(encoded_title) for template in templates]


def load_user_agents():
    """
    Load a list of user agents from a text file.

    :return: List of user agents.
    """
    try:
        with open("user_agents.txt", "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}Error: 'user_agents.txt' file not found.{Style.RESET_ALL}")
        return []


USER_AGENTS = load_user_agents()


def get_random_user_agent():
    """
    Get a random user agent from the list.

    :return: A random user agent string.
    """
    return random.choice(USER_AGENTS) if USER_AGENTS else None


def check_link(link):
    """
    Check the status of a single link using a random user agent.

    :param link: Link to check.
    :return: Tuple of (link, status).
    """
    headers = {}
    user_agent = get_random_user_agent()
    if user_agent:
        headers["User-Agent"] = user_agent

    try:
        response = requests.get(link, headers=headers, timeout=5)
        if response.status_code == 200:
            return link, "Found"
        else:
            return link, "Unsure"
    except requests.RequestException:
        return link, "Unsure"


def check_links(links):
    link_status = {}
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_link = {executor.submit(check_link, link): link for link in links}
        for future in as_completed(future_to_link):
            link, status = future.result()
            link_status[link] = status
    return link_status


if __name__ == "__main__":
    app.run(debug=True)
