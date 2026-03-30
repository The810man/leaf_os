import curses
import time
from typing import List

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from pages.base_page import BasePage
from ui.panels import (
    draw_animation_panel,
    draw_stats_panel,
    draw_graph_panel,
    draw_text,
    rounded_box,
)


class InfoPage(BasePage):
    """Info page showing system stats (CPU, RAM) with animation."""

    def __init__(self):
        super().__init__("info")

    def get_title(self) -> str:
        return " SYSTEM INFO "

    def draw(self, stdscr, y: int, x: int, h: int, w: int,
             monitor: SystemMonitor, animation: AsciiAnimation):
        """Draw the info page with animation and system stats."""
        # Draw animation panel on the left
        left_w = max(44, min(78, int(w * 0.40)))
        right_x = left_w + 1
        right_w = w - right_x - 1

        draw_animation_panel(stdscr, y, x, h - 8, left_w, animation)
        
        # Draw system stats on the right
        cpu = monitor.last_cpu
        ram = monitor.last_ram
        
        draw_stats_panel(stdscr, y, right_x, 6, right_w, cpu, ram)
        draw_graph_panel(stdscr, y + 6, right_x, 9, right_w, " CPU HISTORY ", monitor.cpu_history, cpu)
        draw_graph_panel(stdscr, y + 15, right_x, 9, right_w, " RAM HISTORY ", monitor.ram_history, ram)
        
        # Draw CPU temperature (mock for now)
        temp_y = y + 24
        if temp_y < h - 2:
            rounded_box(stdscr, temp_y, right_x, 6, right_w, " CPU TEMPERATURE ", 1)
            # Mock temperature data
            mock_temp = 45.2
            draw_text(stdscr, temp_y + 2, right_x + 3, f"TEMP {mock_temp:5.1f}°C", 4, True)
            draw_text(stdscr, temp_y + 3, right_x + 3, "Status: NORMAL", 8, True)
