from urllib.parse import urlparse

def convert_runtime(runtime: str) -> str:
    """
    Convert runtime from minutes to hours and minutes format.
    Example: "169 min" -> "169 min (2h 8m)"
    :param runtime: Runtime string from OMDB API (e.g., "169 min").
    :return: Converted runtime string (e.g., "169 min (2h 8m)").
    """
    try:
        minutes = int(runtime.split()[0])
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{minutes} min ({hours}h {remaining_minutes}m)"
    except (ValueError, AttributeError, IndexError):
        return runtime


def extract_website_name(url: str) -> str:
    """
    Extract a localized/friendly website name from a link's URL.
    """
    website_mapping = {
        "130.185.118.151": "Driverays",
        "batch.moe": "Batchindo",
        "hydrahd.me": "HydraHD",
        "moviepire.net": "Moviepire",
        "cinebytv.com": "Cineby TV",
        "pahe.ink": "Pahe",
        "seriesonlinehd.net": "Series Online HD",
        "todaytvseries1.com": "Today TV Series",
        "tv11.idlixku.com": "Idlix",
        "tvshows.ac": "TV Shows",
        "uflix.cc": "uFlix",
        "pencurimovie.bond": "Pencurimovie",
        "vertexmovies.com": "Vertexmovies",
        "ext.to": "ExtraTorrent",
        "subdl.com": "SubDL",
        "subsource.net": "Subsource",
        "emnexmovies.tech": "EmnexMovies",
        "showbox.media": "Showbox",
        "donkey.to": "Donkey",
        "ptflix.cc": "Ptflix",
    }

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
