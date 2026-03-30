import curses
import time
from typing import List

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from pages.base_page import BasePage
from pages.info_page import InfoPage
from pages.mqtt_page import MQTTPage
from pages.plant_status_page import PlantStatusPage
from ui.colors import init_colors
from ui.panels import draw_text, rounded_box, draw_too_small
from ui.commands import process_command


class LeafBoardTUI:
    def __init__(self, animation_path: str = "ascii-frames.json"):
        self.monitor = SystemMonitor()
        self.animation = AsciiAnimation(animation_path)
        self.running = True
        self.command_buffer = ""
        self.output_lines: List[str] = ["Welcome to Leaf Board. Type 'help'."]
        self.last_stats_update = 0.0
        self.stats_interval = 0.20
        
        # Initialize pages
        self.pages: List[BasePage] = [
            InfoPage(),
            MQTTPage(),
            PlantStatusPage(),
        ]
        self.current_page_index = 0

    def draw(self, stdscr):
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        if h < 28 or w < 100:
            draw_too_small(stdscr, h, w)
            return

        now = time.monotonic()
        if now - self.last_stats_update >= self.stats_interval:
            cpu, ram = self.monitor.update()
            self.last_stats_update = now
        else:
            cpu, ram = self.monitor.last_cpu, self.monitor.last_ram

        self.animation.tick()

        # Draw main border with page title
        current_page = self.pages[self.current_page_index]
        page_title = f" LEAF BOARD - {current_page.get_title()} "
        rounded_box(stdscr, 0, 0, h, w, page_title, 1)

        # Draw current page
        current_page.draw(stdscr, 1, 1, h - 9, w - 2, self.monitor, self.animation)

        # Draw command log panel at the bottom
        self._draw_log_panel(stdscr, h - 8, 1, 7, w - 2)

        # Draw footer with navigation hints
        footer = f"Page {self.current_page_index + 1}/{len(self.pages)} │ Enter submit │ Backspace delete │ q quit │ next/prev to navigate"
        draw_text(stdscr, h - 1, max(2, (w - len(footer)) // 2), footer, 7)

        stdscr.refresh()

    def _draw_log_panel(self, win, y, x, h, w):
        """Draw the command log panel."""
        rounded_box(win, y, x, h, w, " COMMAND ", 1)
        usable = h - 3
        lines = self.output_lines[-max(1, usable - 1):]

        for i, line in enumerate(lines[: max(0, usable - 1)]):
            draw_text(win, y + 1 + i, x + 2, line[: max(0, w - 4)], 3)

        prompt = "> " + self.command_buffer
        draw_text(win, y + h - 2, x + 2, prompt[: max(0, w - 4)], 2, True)

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        stdscr.timeout(33)
        init_colors()
        self.monitor.update()

        while self.running:
            self.draw(stdscr)

            try:
                key = stdscr.getch()
                if key == -1:
                    continue
                elif key in (ord("q"),):
                    self.running = False
                elif key in (10, 13, curses.KEY_ENTER):
                    should_continue, new_page_index = process_command(
                        self.command_buffer,
                        self.output_lines,
                        self.monitor,
                        self.animation,
                        self.pages,
                        self.current_page_index
                    )
                    self.running = should_continue
                    self.current_page_index = new_page_index
                    self.command_buffer = ""
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    self.command_buffer = self.command_buffer[:-1]
                elif key == curses.KEY_RIGHT or key == ord("l"):
                    # Next page with right arrow or 'l'
                    self.current_page_index = (self.current_page_index + 1) % len(self.pages)
                elif key == curses.KEY_LEFT or key == ord("h"):
                    # Previous page with left arrow or 'h'
                    self.current_page_index = (self.current_page_index - 1) % len(self.pages)
                else:
                    # Check if current page handles the input
                    current_page = self.pages[self.current_page_index]
                    if hasattr(current_page, 'handle_input'):
                        if current_page.handle_input(key, self.output_lines):
                            continue
                    
                    # Regular character input for command buffer
                    if 32 <= key <= 126:
                        _, width = stdscr.getmaxyx()
                        if len(self.command_buffer) < width - 8:
                            self.command_buffer += chr(key)
            except curses.error:
                pass
