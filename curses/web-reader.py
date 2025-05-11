from curses import window
from dataclasses import dataclass
import curses
import ccolors
from cinput import CommandWindow
from newspaper import Article
import sys, os, subprocess, requests, feedparser
from typing import Type, List, Tuple, Union, Dict, Any

VOICE_NAME = "en-US-AndrewNeural"
DATA_PATH = os.path.expanduser("~/.local/share/web-reader/")
TEXT_DATA_PATH = os.path.join(DATA_PATH, "text")
AUDIO_DATA_PATH = os.path.join(DATA_PATH, "audio")

@dataclass
class widget:
    win: window
    color: int
    title: str = ""
    active: bool = False

layout: Dict[str, widget] = {}
cw = CommandWindow()
main_commands = [('d', 'downloads'),
             ('s', 'select')]
playing_commands = [('p', 'play'),
             ('a', 'pause'),
             ('s', 'stop'),
             ('n', 'next'),
             ('b', 'previous')]

num_downloads = 0


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

def draw_widget(win, color, title=""):
    """
    Simple wrapper to draw a box around a window
    with the given attributes.
    """
    win.attron(color)
    win.box() 
    
    win.attron(curses.A_BOLD)
    win.addstr(0, 1, f"{title}")
    win.attroff(curses.A_BOLD)

    win.attroff(color)

def draw(stdscr: curses.window):
    stdscr.refresh()
    # cw.help(main_commands)
    # cw._draw_widget()
    for widget in layout.values():
        draw_widget(widget.win, widget.color, widget.title)
        widget.win.refresh()
        # win.refresh()

def create_layout(stdscr: curses.window):
    height, width = stdscr.getmaxyx()
    EIGHTH = width // 8
    Y_PAD, X_PAD = 1, 1

    left_w = 5 * EIGHTH
    x, y = 0, 0
    layout["main"] = widget(stdscr.subwin(height-3, width, y, x), ccolors.DARK_GREY, "welcome!")

    x += 2 * X_PAD # move to top left of inner window, get out from main box
    y += Y_PAD # move to top left of inner window
    layout["reader"] = widget(stdscr.subwin(height-5, left_w, y, x), ccolors.WHITE, "reader:")

    x += left_w + (X_PAD) # move past reader window, horizontally
    right_w = width - x - (2 * X_PAD)
    download_height = min(max(3, num_downloads), 5)
    layout["downloads"] = widget(stdscr.subwin(download_height, right_w, y, x), ccolors.WHITE, "downloads:")
    y += download_height
    layout["browse"] = widget(stdscr.subwin(height - y - download_height - Y_PAD, right_w, y, x), ccolors.WHITE, "browse:", True)
    # layout["main"] = widget(stdscr.subwin(height-3, width, 0, 0), ccolors.DARK_GREY)
    # layout["reader"] = widget(stdscr.subwin(height-5, 5 * EIGHTH - (2 * X_PAD), 1, 2), ccolors.WHITE)
    # layout["downloads"] = widget(stdscr.subwin(5, 3 * EIGHTH - 4, 1, 5 * EIGHTH - X_PAD), ccolors.WHITE)

def main(stdscr: curses.window):
    stdscr = setup_curses()
    create_layout(stdscr)
    cw.help(main_commands)

    keymap = {
        "q":    lambda: exit(0),
        "h":    lambda: cw.help(main_commands),
        "i":    lambda: cw.get_input(main_commands),
        "d":    lambda: select_downloads()
    }

    while True: # Running loop
        draw(stdscr)
        # cw.help(main_commands)
        # cw.make_selection("actions:", ["play", "pause", "stop", "next", "previous"])
        key = stdscr.getkey()
        if key in keymap:
            keymap[key]()
        # else:
            # draw_widget(stdscr, ccolors.WHITE)

if __name__ == "__main__":
    curses.wrapper(main)
