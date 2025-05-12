from newspaper import Article
import sys, os, subprocess, requests, feedparser

import logging
# Configure logging
logging.basicConfig(filename='scraper-debug.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

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
            text_file.write(article.text)
        subprocess.run(["edge-playback", "--file", str(text_filepath), "--voice", VOICE_NAME, "--write-media", str(audio_filepath)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def create_mp3(pull=False):
    headers = {"User-Agent": "Mozilla/5.0"}
    for rss_feed in rss_feeds:
        resp = requests.get(rss_feeds[rss_feed], headers=headers)
        feeds = feedparser.parse(resp.content)

        if pull:
            for feed in feeds.entries:
                if not os.path.isfile(os.path.join(AUDIO_PATH, f"{get_sanitized(feed.title)}.mp3")):
                    choice = input().lower()
                    if choice == "q":
                        sys.exit(0)
                    if choice == "y":
                        process_article(feed.link)

        else: 
            article_link = feeds.entries[int(input()) - 1].link
            process_article(article_link)

def get_audio_files():
    return [item for item in os.listdir(AUDIO_PATH)]

def get_text_files():
    return [item for item in os.listdir(TEXT_PATH)]

def init():
    os.makedirs(TEXT_PATH, exist_ok=True)
    os.makedirs(AUDIO_PATH, exist_ok=True)
