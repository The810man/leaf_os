import curses


def init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
    except curses.error:
        pass

    bg = -1
    white = curses.COLOR_WHITE
    yellow = curses.COLOR_YELLOW
    green = curses.COLOR_GREEN
    red = curses.COLOR_RED
    cyan = curses.COLOR_CYAN
    magenta = curses.COLOR_MAGENTA

    curses.init_pair(1, yellow, bg)   # border
    curses.init_pair(2, yellow, bg)   # title
    curses.init_pair(3, white, bg)    # normal text
    curses.init_pair(4, green, bg)    # low usage
    curses.init_pair(5, yellow, bg)   # medium usage
    curses.init_pair(6, red, bg)      # high usage
    curses.init_pair(7, cyan, bg)     # muted
    curses.init_pair(8, green, bg)    # animation
    curses.init_pair(9, magenta, bg)  # alert
