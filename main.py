#!/usr/bin/env python3
import curses

from tui import LeafBoardTUI


def main():
    curses.wrapper(LeafBoardTUI("ascii-frames-globe.json").run)


if __name__ == "__main__":
    main()
