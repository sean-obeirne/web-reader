import colors
from newspaper import Article
import sys, os, subprocess, requests, feedparser


VOICE_NAME = "en-US-AndrewNeural"
WEB_READER_PATH = os.path.expanduser("~/.local/share/web-reader/")
TEXT_PATH = os.path.join(WEB_READER_PATH, "text")
AUDIO_PATH = os.path.join(WEB_READER_PATH, "audio")


rss_feeds = {
    # "devto_linux": "https://dev.to/feed/tag/linux",
    # "devto_ben": "https://dev.to/feed/ben",
    "substack": "https://bytebytego.substack.com/feed",
    # "substack_exponential_view": "https://www.exponentialview.co/feed",
    # "hn_linux": "https://hnrss.org/newest?q=linux",
    # "ars_technica": "https://arstechnica.com/feed/",
    # "the_verge_tech": "https://www.theverge.com/tech/rss/index.xml",
    # "drew_devault_blog": "https://drewdevault.com/blog/index.xml"
}


def get_sanitized(filename):
    # Remove any characters that are not alphanumeric
    # return ''.join(c if c.isalnum() or c == '.' else '-' for c in filename).strip()
    return filename.replace(" ", "-").replace("/", "-")

def get_article(url):
    article = Article(url)
    article.download()
    article.parse()
    article.title = get_sanitized(article.title)
    return article

def process_article(url, redownload=False):
    article = get_article(url)
    text_filepath = os.path.join(TEXT_PATH, f"{article.title}")
    audio_filepath = os.path.join(AUDIO_PATH, f"{article.title}.mp3")

    if not os.path.isfile(audio_filepath) or redownload:
        with open(text_filepath, 'w') as text_file:
            colors.print_color(f"{article.title}\n", "italic,cyan")
            colors.print_color(f"\tCreating text file...\t    ", "yellow")
            text_file.write(article.text)
            colors.print_color(f"Done,\t{len(article.text.split())} words\n", "green")


        # with open(audio_filepath, 'w') as audio_file:
        colors.print_color(f"\tCreating audio file...\t    ", "yellow")
        subprocess.run(["edge-playback", "--file", str(text_filepath), "--voice", VOICE_NAME, "--write-media", str(audio_filepath)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        colors.print_color(f"Done!\n", "green")

def create_mp3(pull=False):
    headers = {"User-Agent": "Mozilla/5.0"}
    for rss_feed in rss_feeds:
        colors.print_color(f"\tPulling ", "yellow")
        colors.print_color(f"{rss_feed}", "italic,yellow")
        colors.print_color(f" RSS feed...\t    ", "yellow")
        resp = requests.get(rss_feeds[rss_feed], headers=headers)
        colors.print_color(f"Done!\n\n\n", "green")

        feeds = feedparser.parse(resp.content)
        
        if pull:
            for feed in feeds.entries:
                if not os.path.isfile(os.path.join(AUDIO_PATH, f"{get_sanitized(feed.title)}.mp3")):
                    colors.print_color(f"{feed.title}\n", "italic,cyan")
                    colors.print_color(f"{feed.link}\n\n", "white")
                    colors.print_color(f"  Download article [y/N/q]? ", "bold,red")
                    choice = input().lower()
                    if choice == "q":
                        colors.print_color("Exiting...", "bold,red")
                        sys.exit(0)
                    if choice == "y":
                        process_article(feed.link)

        else: 
            colors.print_color(f"  Pick article:\n", "bold,red")
            for i, feed in enumerate(feeds.entries):
                colors.print_color(f"\t{i+1}.", "bold,green")
                colors.print_color(f"\t{feed.title}\n", "italic,cyan")

            colors.print_color(f"  Enter article number: ", "bold,red")
            article_link = feeds.entries[int(input()) - 1].link
            print(f"\t{article_link}\n\n")
            process_article(article_link)

def main():
    if len(sys.argv) != 2:
        print("Usage: python web_reader.py <listen|create|sync>")
        sys.exit(1)
    os.makedirs(TEXT_PATH, exist_ok=True)
    os.makedirs(AUDIO_PATH, exist_ok=True)

    if sys.argv[1] != "listen":
        create_mp3(sys.argv[1] == "sync")

    file_to_read = os.path.join(AUDIO_PATH, subprocess.run(["fzf", "--prompt", "Select a file to listen to: "], cwd=AUDIO_PATH, capture_output=True, text=True).stdout.strip())
    print(f"{file_to_read}")
    subprocess.run(["mpv", file_to_read], check=True)

if __name__ == "__main__":
    main()
