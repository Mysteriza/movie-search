import json
import urllib.parse
from typing import List, Dict, Any
from utils.helpers import extract_website_name

def load_templates() -> Dict[str, List[str]]:
    """Load templates from file, returning a default structure if not found."""
    try:
        with open("templates.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "download_templates": [],
            "tvshow_download_templates": [],
            "streaming_templates": [],
            "tvshow_templates": [],
            "torrent_templates": [],
            "subtitle_templates": [],
        }

TEMPLATES_CACHE = load_templates()

def generate_links(movie_title: str, templates: List[str]) -> List[str]:
    """Generate links based on a list of template strings."""
    cleaned_title = movie_title.replace("'", "").replace('"', "").replace(":", " ")
    cleaned_title = " ".join(cleaned_title.split())

    links = []
    for template in templates:
        if "seriesonlinehd.net" in template:
            formatted_title = cleaned_title.replace(" ", "-").lower()
            encoded_title = urllib.parse.quote(formatted_title, safe="")
            links.append(template.format(encoded_title))
        else:
            encoded_title = urllib.parse.quote(cleaned_title, safe="")
            links.append(template.format(encoded_title))

    return links

def prepare_link_data(links: List[str]) -> List[Dict[str, str]]:
    """Format strings into dict objects with name and url."""
    return [{"name": extract_website_name(link), "url": link} for link in links]

def get_all_movie_links(movie_title: str) -> Dict[str, List[Dict[str, str]]]:
    """Generate all categorized movie links for a given title."""
    return {
        "downloads": prepare_link_data(generate_links(movie_title, TEMPLATES_CACHE.get("download_templates", []))),
        "tvshow_downloads": prepare_link_data(generate_links(movie_title, TEMPLATES_CACHE.get("tvshow_download_templates", []))),
        "streaming": prepare_link_data(generate_links(movie_title, TEMPLATES_CACHE.get("streaming_templates", []))),
        "tvshows": prepare_link_data(generate_links(movie_title, TEMPLATES_CACHE.get("tvshow_templates", []))),
        "torrents": prepare_link_data(generate_links(movie_title, TEMPLATES_CACHE.get("torrent_templates", []))),
        "subtitles": prepare_link_data(generate_links(movie_title, TEMPLATES_CACHE.get("subtitle_templates", []))),
    }
