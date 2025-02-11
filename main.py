import json
import urllib.parse
import requests
import webbrowser
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

# Inisialisasi colorama
init(autoreset=True)


class MovieLinkGenerator:
    def __init__(self):
        # Load template URLs from JSON file
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
        Menghasilkan daftar link berdasarkan judul film atau subtitle.

        :param movie_title: Judul film/subtitle yang akan digunakan sebagai query pencarian.
        :param templates: List of URL templates to use.
        :return: List of generated links.
        """
        # Encode judul film/subtitle untuk URL (mengganti spasi dengan '+' atau '%20')
        encoded_title = urllib.parse.quote_plus(movie_title)

        # Generate link untuk setiap template URL
        links = [template.format(encoded_title) for template in templates]
        return links

    def check_link(self, link):
        """
        Memeriksa status sebuah link secara individual.

        :param link: Link yang akan diperiksa.
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
        Memeriksa semua link secara simultan menggunakan concurrency.

        :param links: List of links to check.
        :return: Dictionary with link as key and status as value.
        """
        print(f"\n{Fore.CYAN}Checking links... Please wait.{Style.RESET_ALL}")
        link_status = {}

        # Gunakan ThreadPoolExecutor untuk menjalankan pengecekan secara paralel
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
        Menampilkan semua link dengan statusnya.

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
        Membuka semua link di browser pengguna.

        :param links: List of links to open.
        """
        if not links:
            print(f"{Fore.RED}No links to open in the browser.{Style.RESET_ALL}")
            return

        choice = (
            input(
                f"\n{Fore.GREEN}Do you want to open all links in your browser? (y/n): {Style.RESET_ALL}"
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


# Contoh penggunaan
if __name__ == "__main__":
    generator = MovieLinkGenerator()

    # Input judul film dari pengguna
    print(f"{Fore.MAGENTA}Welcome to the Movie Link Generator!{Style.RESET_ALL}")
    movie_title = input(f"{Fore.GREEN}Masukkan judul film: {Style.RESET_ALL}").strip()

    # Generate link untuk pencarian film
    movie_links = generator.generate_links(
        movie_title, generator.templates["movie_templates"]
    )

    # Cek status link untuk pencarian film
    movie_link_status = generator.check_links(movie_links)

    # Tampilkan hasil pencarian film
    generator.display_links(movie_link_status, "Generated Links for Movies")

    # Generate link untuk pencarian subtitle
    subtitle_links = generator.generate_links(
        movie_title, generator.templates["subtitle_templates"]
    )

    # Cek status link untuk pencarian subtitle
    subtitle_link_status = generator.check_links(subtitle_links)

    # Tampilkan hasil pencarian subtitle
    generator.display_links(subtitle_link_status, "Generated Links for Subtitles")

    # Gabungkan semua link (film dan subtitle)
    all_links = list(movie_link_status.keys()) + list(subtitle_link_status.keys())

    # Tanyakan apakah ingin membuka semua link di browser
    generator.open_all_links_in_browser(all_links)
