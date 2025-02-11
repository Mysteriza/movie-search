import urllib.parse
from colorama import Fore, Style, init

# Inisialisasi colorama
init(autoreset=True)


class MovieLinkGenerator:
    def __init__(self):
        # Daftar template URL dari berbagai situs web
        self.url_templates = [
            "https://tv7.idlix.asia/search/{}",
            "https://pahe.ink/?s={}",
            "https://130.185.118.151/?s={}&post_type=post",
            "https://ww73.pencurimovie.bond/?s={}",
            "https://hydrahd.me/index.php?menu=search&query={}",
            "https://broflix.ci/search?text={}",
            "https://freek.to/search?query={}",
        ]

    def generate_links(self, movie_title):
        """
        Menghasilkan daftar link berdasarkan judul film yang diinput.

        :param movie_title: Judul film yang akan digunakan sebagai query pencarian.
        :return: List of generated links.
        """
        # Encode judul film untuk URL (mengganti spasi dengan '+' atau '%20')
        encoded_title = urllib.parse.quote_plus(movie_title)

        # Generate link untuk setiap template URL
        links = [template.format(encoded_title) for template in self.url_templates]
        return links

    def add_url_template(self, new_template):
        """
        Menambahkan template URL baru ke dalam daftar.

        :param new_template: Template URL baru yang akan ditambahkan.
        """
        if new_template not in self.url_templates:
            self.url_templates.append(new_template)
            print(
                f"{Fore.GREEN}Template URL '{new_template}' berhasil ditambahkan.{Style.RESET_ALL}"
            )
        else:
            print(f"{Fore.YELLOW}Template URL sudah ada dalam daftar.{Style.RESET_ALL}")

    def display_links(self, links):
        """
        Menampilkan semua link yang telah di-generate dengan format yang lebih menarik.

        :param links: List of links to display.
        """
        print("\n" + "=" * 50)
        print(f"{Fore.CYAN}Generated Links for Your Movie Search:{Style.RESET_ALL}")
        print("=" * 50)

        for idx, link in enumerate(links, start=1):
            print(f"{Fore.YELLOW}{idx}. {Fore.BLUE}{link}{Style.RESET_ALL}")

        print("=" * 50)


# Contoh penggunaan
if __name__ == "__main__":
    generator = MovieLinkGenerator()

    # Input judul film dari pengguna
    print(f"{Fore.MAGENTA}Welcome to the Movie Link Generator!{Style.RESET_ALL}")
    movie_title = input(f"{Fore.GREEN}Masukkan judul film: {Style.RESET_ALL}").strip()

    # Generate link
    links = generator.generate_links(movie_title)

    # Tampilkan hasil
    generator.display_links(links)

    # Contoh penambahan template URL baru
    # generator.add_url_template("https://example.com/search?query={}")
