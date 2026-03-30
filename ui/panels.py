import curses
import time
from typing import List, Deque

from renderers.frame_utils import fit_frame_to_box
from renderers.graph_renderer import GraphRenderer


def draw_text(win, y, x, text, color=3, bold=False):
    try:
        attr = curses.color_pair(color)
        if bold:
            attr |= curses.A_BOLD
        max_y, max_x = win.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            safe = text[: max(0, max_x - x)]
            win.addstr(y, x, safe, attr)
    except curses.error:
        pass


def rounded_box(win, y, x, h, w, title="", color=1):
    if h < 2 or w < 2:
        return
    try:
        win.addstr(y, x, "╭" + "─" * (w - 2) + "╮", curses.color_pair(color))
        for i in range(1, h - 1):
            win.addstr(y + i, x, "│", curses.color_pair(color))
            win.addstr(y + i, x + w - 1, "│", curses.color_pair(color))
        win.addstr(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", curses.color_pair(color))
        if title and w > len(title) + 4:
            label = f" {title} "
            tx = x + max(2, (w - len(label)) // 2)
            draw_text(win, y, tx, label, 2, True)
    except curses.error:
        pass


def usage_color(value: float) -> int:
    if value >= 80:
        return 6
    if value >= 50:
        return 5
    return 4


def draw_animation_panel(win, y, x, h, w, animation):
    rounded_box(win, y, x, h, w, " ANIMATION ", 1)

    inner_y = y + 1
    inner_x = x + 2
    inner_h = h - 2
    inner_w = w - 4

    if inner_h < 4 or inner_w < 12:
        draw_text(win, y + 1, x + 2, "Panel too small", 9, True)
        return

    fitted = fit_frame_to_box(animation.current_frame(), inner_w, inner_h, char_aspect=2.0)
    if not fitted:
        return

    frame_h = len(fitted)
    frame_w = max((len(line) for line in fitted), default=0)
    start_y = inner_y + max(0, (inner_h - frame_h) // 2)
    start_x = inner_x + max(0, (inner_w - frame_w) // 2)

    for i, line in enumerate(fitted):
        color = 8 if i < frame_h - 2 else 7
        draw_text(win, start_y + i, start_x, line, color)


def draw_stats_panel(win, y, x, h, w, cpu, ram):
    rounded_box(win, y, x, h, w, " SYSTEM ", 1)
    draw_text(win, y + 2, x + 3, f"CPU  {cpu:5.1f}%", usage_color(cpu), True)
    draw_text(win, y + 3, x + 3, f"RAM  {ram:5.1f}%", usage_color(ram), True)
    draw_text(win, y + 2, x + w - 18, time.strftime("%H:%M:%S"), 7)
    draw_text(win, y + 3, x + w - 18, "LIVE", 8, True)


def draw_graph_panel(win, y, x, h, w, title, data, current_value):
    rounded_box(win, y, x, h, w, title, 1)

    inner_y = y + 1
    inner_x = x + 2
    inner_h = h - 3
    inner_w = w - 4

    if inner_h < 4 or inner_w < 12:
        return

    plot_h = max(1, inner_h - 2)
    columns = GraphRenderer.mini_columns(data, inner_w, plot_h)

    color = usage_color(current_value)
    for i, row in enumerate(columns):
        draw_text(win, inner_y + i, inner_x, row, color)

    baseline = "─" * inner_w
    draw_text(win, inner_y + plot_h, inner_x, baseline, 7)

    spark = GraphRenderer.sparkline(data, max(10, inner_w - 10))
    label = f"{current_value:5.1f}% "
    spark_space = max(0, inner_w - len(label))
    draw_text(win, y + h - 2, x + 2, spark[:spark_space], 2)
    draw_text(win, y + h - 2, x + 2 + inner_w - len(label), label, color, True)


def draw_log_panel(win, y, x, h, w, output_lines, command_buffer):
    rounded_box(win, y, x, h, w, " COMMAND ", 1)
    usable = h - 3
    lines = output_lines[-max(1, usable - 1):]

    for i, line in enumerate(lines[: max(0, usable - 1)]):
        draw_text(win, y + 1 + i, x + 2, line[: max(0, w - 4)], 3)

    prompt = "> " + command_buffer
    draw_text(win, y + h - 2, x + 2, prompt[: max(0, w - 4)], 2, True)


def draw_too_small(stdscr, h, w):
    rounded_box(stdscr, 0, 0, h, w, " LEAF BOARD ", 1)
    draw_text(stdscr, 2, 3, "Terminal too small", 9, True)
    draw_text(stdscr, 4, 3, f"Current size: {w}x{h}", 3)
    draw_text(stdscr, 5, 3, "Need at least about 100x28", 3)
    stdscr.refresh()
