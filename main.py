import json
import urllib.parse
import requests
import webbrowser
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize colorama
init(autoreset=True)


class MovieLinkGenerator:
    def __init__(self):
        # Load templates from JSON file
        self.templates = self.load_templates()

    def load_templates(self):
        """
        Load templates from a JSON file.

        :return: Dictionary containing movie and subtitle templates.
        """
        try:
            with open("templates.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"{Fore.RED}Error: 'templates.json' file not found.{Style.RESET_ALL}")
            exit(1)
        except json.JSONDecodeError:
            print(
                f"{Fore.RED}Error: Invalid JSON format in 'templates.json'.{Style.RESET_ALL}"
            )
            exit(1)

    def generate_links(self, movie_title, templates):
        """
        Generate a list of links based on the movie title or subtitle.

        :param movie_title: Movie/subtitle title to use as a search query.
        :param templates: List of URL templates to use.
        :return: List of generated links.
        """
        # Encode the movie/subtitle title for the URL (replace spaces with '+' or '%20')
        encoded_title = urllib.parse.quote_plus(movie_title)

        # Generate links for each template
        links = [template.format(encoded_title) for template in templates]
        return links

    def check_link(self, link):
        """
        Check the status of a single link.

        :param link: Link to check.
        :return: Tuple of (link, status).
        """
        try:
            response = requests.get(link, timeout=5)
            if response.status_code == 200:
                return link, "Found"
            else:
                return link, "Unsure"
        except requests.RequestException:
            return link, "Error (Timeout or Unreachable)"

    def check_links(self, links):
        """
        Check all links simultaneously using concurrency.

        :param links: List of links to check.
        :return: Dictionary with link as key and status as value.
        """
        print(f"\n{Fore.CYAN}Checking links... Please wait.{Style.RESET_ALL}")
        link_status = {}

        # Use ThreadPoolExecutor to check links concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_link = {
                executor.submit(self.check_link, link): link for link in links
            }
            for future in as_completed(future_to_link):
                link, status = future.result()
                link_status[link] = status

        return link_status

    def display_links(self, link_status, title):
        """
        Display all links with their status.

        :param link_status: Dictionary with link as key and status as value.
        :param title: Title to display before the links.
        """
        print("\n" + "=" * 50)
        print(f"{Fore.CYAN}{title}:{Style.RESET_ALL}")
        print("=" * 50)

        for idx, (link, status) in enumerate(link_status.items(), start=1):
            if status == "Found":
                print(
                    f"{Fore.YELLOW}{idx}. {Fore.GREEN}[{status}] {Fore.BLUE}{link}{Style.RESET_ALL}"
                )
            elif status == "Unsure":
                print(
                    f"{Fore.YELLOW}{idx}. {Fore.YELLOW}[{status}] {Fore.BLUE}{link}{Style.RESET_ALL}"
                )
            else:
                print(
                    f"{Fore.YELLOW}{idx}. {Fore.MAGENTA}[{status}] {Fore.BLUE}{link}{Style.RESET_ALL}"
                )

        print("=" * 50)

    def open_all_links_in_browser(self, links):
        """
        Open all links in the user's browser.

        :param links: List of links to open.
        """
        if not links:
            print(f"{Fore.RED}No links to open in the browser.{Style.RESET_ALL}")
            return

        choice = (
            input(
                f"\n{Fore.GREEN}Do you want to open all links in your browser? (Y/n): {Style.RESET_ALL}"
            )
            .strip()
            .lower()
        )
        if choice == "y":
            for link in links:
                webbrowser.open(link)
            print(
                f"{Fore.GREEN}All links have been opened in your browser.{Style.RESET_ALL}"
            )
        else:
            print(f"{Fore.YELLOW}Opening links canceled.{Style.RESET_ALL}")


# Example usage
if __name__ == "__main__":
    generator = MovieLinkGenerator()

    # Input movie title from the user
    print(f"{Fore.MAGENTA}Welcome to the Movie Link Generator!{Style.RESET_ALL}")
    movie_title = input(f"{Fore.GREEN}Enter the movie title: {Style.RESET_ALL}").strip()

    # Generate links for movie search
    movie_links = generator.generate_links(
        movie_title, generator.templates["movie_templates"]
    )

    # Check the status of movie links
    movie_link_status = generator.check_links(movie_links)

    # Display movie search results
    generator.display_links(movie_link_status, "Generated Links for Movies")

    # Generate links for subtitle search
    subtitle_links = generator.generate_links(
        movie_title, generator.templates["subtitle_templates"]
    )

    # Check the status of subtitle links
    subtitle_link_status = generator.check_links(subtitle_links)

    # Display subtitle search results
    generator.display_links(subtitle_link_status, "Generated Links for Subtitles")

    # Combine all links (movies and subtitles)
    all_links = list(movie_link_status.keys()) + list(subtitle_link_status.keys())

    # Ask if the user wants to open all links in the browser
    generator.open_all_links_in_browser(all_links)
