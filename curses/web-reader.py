import scraper

from curses import window
import curses
import textwrap
import ccolors
from cinput import CommandWindow

from newspaper import Article
import sys
import os
import subprocess
import requests
import feedparser
from typing import Type, List, Tuple, Union, Dict, Any

import logging
# Configure logging
logging.basicConfig(filename='web-reader-debug.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

VOICE_NAME = "en-US-AndrewNeural"
DATA_PATH = os.path.expanduser("~/.local/share/web-reader/")
TEXT_DATA_PATH = os.path.join(DATA_PATH, "text")
AUDIO_DATA_PATH = os.path.join(DATA_PATH, "audio")

MAX_AUDIO_FILES = 12

class Widget:
    win: window
    name: str
    color: int
    title: str = ""
    active: bool = False
    content_lines: List[str] = []
    top: int = 0
    content_rows: int = 0
    # content_lines: str = """
    # This is a big wall of text to render within a widget at some point in time which may or may not be a certain time of which it might or might not be convenient
    # """

    def __init__(self, win: window, name: str, color: int, title: str = "", content_lines: List[str] = []):
        self.win = win
        self.y, self.x = win.getbegyx()
        self.height, self.width = win.getmaxyx()
        self.name = name
        self.color = color
        self.title = title
        self.content_lines = content_lines
        self.top = 0
        self.content_rows = len(content_lines)

    def activate(self):
        self.color = ccolors.GREEN

    def deactivate(self):
        self.color = ccolors.WHITE

    def extend(self):
        self.content_rows += 1
        self.win.resize(self.content_rows + 2, self.width)

    def drop(self):
        self.win.move(self.y + 1, self.x)

layout: Dict[str, Widget] = {}

cw = CommandWindow()

MAIN_COMMANDS = [('d', 'audio_files'),
             ('s', 'select')]

PLAYING_COMMANDS = [('p', 'play'),
             ('a', 'pause'),
             ('s', 'stop'),
             ('n', 'next'),
             ('b', 'previous')]

rotation = ["reader", "audio_files", "text_files"]
rotation_index = 0

STATE_MAIN = 0
STATE_READER = 1
STATE_DOWNLOADS = 2
STATE_BROWSER = 3
state = STATE_MAIN


def setup_curses():
    """
    Initialise curses, turn on colors, configure terminal state,
    and return the main window (stdscr).
    """
    stdscr = curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    ccolors.init_16_colors()

    stdscr.clear()
    curses.curs_set(0)       # hide cursor
    curses.noecho()          # don’t echo input
    curses.set_escdelay(1)   # make ESC key more responsive
    stdscr.keypad(True)      # enable arrow keys
    stdscr.refresh()
    return stdscr

def rotate():
    global rotation_index
    layout[rotation[rotation_index % len(rotation)]].deactivate()
    rotation_index += 1
    layout[rotation[rotation_index % len(rotation)]].activate()

def state_swich(new_state: int):
    global state
    state = new_state


def draw_widget(widget: Widget, max_height: int=0):
    widget.win.clear()

    widget.win.attron(widget.color)
    widget.win.attron(curses.A_BOLD)
    widget.win.box() 
    widget.win.addstr(0, 1, f"{widget.title}")
    widget.win.attroff(curses.A_BOLD)
    widget.win.attroff(widget.color)

    if widget.name == "reader":
        with open("/home/sean/.local/share/web-reader/text/Azure-storae-service", "r") as f:
            widget.content_lines = f.read().splitlines()
        lines = textwrap.wrap("".join(widget.content_lines), width=widget.win.getmaxyx()[1] - 2)
        for i, line in enumerate(lines):
            widget.win.addstr(i + 1, 1, line)
    elif widget.name == "audio_files":
        widget.content_lines = process_files("audio_files", max_height)
        for i, processed_file in enumerate(widget.content_lines):
            if processed_file not in widget.content_lines:
                widget.content_lines.append(processed_file)
            widget.win.addstr(i + 1, 1, widget.content_lines[i])
    elif widget.name == "text_files":
        widget.content_lines = process_files("text_files", max_height)
        log.info(max_height)
        for i, processed_file in enumerate(widget.content_lines):
            if processed_file not in widget.content_lines:
                widget.content_lines.append(processed_file)
            widget.win.addstr(i + 1, 1, widget.content_lines[i])

def process_files(widget_name: str, height: int=0):
    files = scraper.get_audio_files() if widget_name == "audio_files" else scraper.get_text_files()
    num_downloads = len(files)
    download_height = min(max(2, num_downloads), height)
    files_to_show = files[:download_height]
    width = layout[widget_name].win.getmaxyx()[1] - 2

    processed_files = []
    for file in files_to_show:
        file = file.replace(".mp3", "")
        if len(file) > width - 2:
            file = file[:width - 3] + "..."
        processed_files.append(file)
    return processed_files

def draw(stdscr: curses.window):
    stdscr.refresh()
    height = stdscr.getmaxyx()[0]
    for widget in layout.values():
        draw_widget(widget, height // 2)
        widget.win.refresh()
        # win.refresh()

def create_layout(stdscr: curses.window):
    height, width = stdscr.getmaxyx()
    EIGHTH = width // 8
    Y_PAD, X_PAD = 0, 1

    left_w = 5 * EIGHTH
    x, y = 0, 0
    # layout["main"] = Widget(stdscr.subwin(height-3, width, y, x), ccolors.DARK_GREY, "welcome!")

    # x += X_PAD # move to top left of inner window, get out from main box
    y += Y_PAD # move to top left of inner window
    layout["reader"] = Widget(stdscr.subwin(height-3, left_w, y, x), "reader", ccolors.WHITE, "Reader:", [])
    layout["reader"].activate() # activate reader window first
    draw_widget(layout["reader"], height)

    x += left_w + (X_PAD) # move past reader window, horizontally
    right_w = width - x
    layout["audio_files"] = Widget(stdscr.subwin(MAX_AUDIO_FILES + 2, right_w, y, x), "audio_files", ccolors.WHITE, "Audio Files:", [])
    draw_widget(layout["audio_files"], MAX_AUDIO_FILES + 2)

    y += MAX_AUDIO_FILES + 2
    layout["text_files"] = Widget(stdscr.subwin(height - MAX_AUDIO_FILES - 5, right_w, y, x), "text_files", ccolors.WHITE, "Text Files:", [])
    log.info(height - MAX_AUDIO_FILES - 3)
    draw_widget(layout["text_files"], 5)


def main(stdscr: curses.window):
    scraper.init()

    stdscr = setup_curses()
    create_layout(stdscr)
    cw.help(MAIN_COMMANDS)

    with open("testfile", "r") as f:
        layout["reader"].content_lines = f.read().splitlines()

    keymap = {
        "q":    lambda: exit(0),
        "h":    lambda: cw.help(MAIN_COMMANDS),
        "d":    lambda: cw.help(PLAYING_COMMANDS),
        "\t":   lambda: rotate(),
        "i":    lambda: cw.get_input("test "),
        # "d":    lambda: select_downloads()
    }

    while True: # Running loop
        draw(stdscr)
        key = stdscr.getkey()
        if key in keymap:
            keymap[key]()
        else:
            pass

if __name__ == "__main__":
    curses.wrapper(main)
