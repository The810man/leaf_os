#!/usr/bin/env python3
import curses
import json
import time
import psutil
from pathlib import Path
from collections import deque
from typing import Deque, List, Tuple, Any


class SystemMonitor:
    def __init__(self, history_size: int = 120):
        self.cpu_history: Deque[float] = deque(maxlen=history_size)
        self.ram_history: Deque[float] = deque(maxlen=history_size)
        self.last_cpu = 0.0
        self.last_ram = 0.0

    def update(self) -> Tuple[float, float]:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        self.last_cpu = cpu
        self.last_ram = ram
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        return cpu, ram


class AsciiAnimation:
    def __init__(self, json_path: str, fallback_fps: float = 12.0):
        self.json_path = Path(json_path)
        self.frames: List[List[str]] = []
        self.frame_index = 0
        self.last_advance = 0.0
        self.frame_duration = 1.0 / fallback_fps
        self.max_width = 0
        self.max_height = 0
        self.load()

    def load(self):
        with self.json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        frames = self._extract_frames(data)
        if not frames:
            raise ValueError("No frames found in ascii animation json")

        self.frames = [self._normalize_frame(frame) for frame in frames]

        fps = self._extract_fps(data)
        if fps and fps > 0:
            self.frame_duration = 1.0 / fps

        self._measure_frames()

    def _extract_frames(self, data: Any) -> List[Any]:
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ("frames", "ascii_frames", "images", "animation"):
                if key in data and isinstance(data[key], list):
                    return data[key]

        return []

    def _extract_fps(self, data: Any) -> float | None:
        if not isinstance(data, dict):
            return None

        for key in ("fps", "frame_rate", "framerate"):
            value = data.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return float(value)

        delay = data.get("frame_duration") or data.get("delay")
        if isinstance(delay, (int, float)) and delay > 0:
            if delay > 1:
                return 1.0 / (delay / 1000.0)
            return 1.0 / float(delay)

        return None

    def _normalize_frame(self, frame: Any) -> List[str]:
        if isinstance(frame, str):
            return frame.splitlines()

        if isinstance(frame, list):
            return [str(line).rstrip("\n") for line in frame]

        if isinstance(frame, dict):
            for key in ("content", "frame", "text", "ascii"):
                value = frame.get(key)
                if isinstance(value, str):
                    return value.splitlines()
                if isinstance(value, list):
                    return [str(line).rstrip("\n") for line in value]

        return ["[invalid frame]"]

    def _measure_frames(self):
        self.max_height = 0
        self.max_width = 0
        for frame in self.frames:
            self.max_height = max(self.max_height, len(frame))
            self.max_width = max(self.max_width, max((len(line) for line in frame), default=0))

    def tick(self):
        now = time.monotonic()
        if now - self.last_advance >= self.frame_duration:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_advance = now

    def current_frame(self) -> List[str]:
        if not self.frames:
            return ["[no frames]"]
        return self.frames[self.frame_index]


class GraphRenderer:
    BARS = "▁▂▃▄▅▆▇█"

    @staticmethod
    def render_bars(data: Deque[float], width: int) -> str:
        values = list(data)[-width:]
        if not values:
            return " " * width

        out = []
        for v in values:
            idx = min(len(GraphRenderer.BARS) - 1, max(0, int((v / 100.0) * (len(GraphRenderer.BARS) - 1))))
            out.append(GraphRenderer.BARS[idx])
        return "".join(out)

    @staticmethod
    def render_area(data: Deque[float], width: int, height: int) -> List[List[Tuple[str, int]]]:
        values = list(data)[-width:]
        if not values:
            return [[(" ", 0) for _ in range(width)] for _ in range(height)]

        canvas = [[(" ", 0) for _ in range(width)] for _ in range(height)]

        for x, v in enumerate(values):
            filled = int((v / 100.0) * height)
            for y in range(height):
                draw_y = height - 1 - y
                if y < filled:
                    ratio = y / max(1, height - 1)
                    if ratio < 0.33:
                        color = 4
                    elif ratio < 0.66:
                        color = 5
                    else:
                        color = 6
                    canvas[draw_y][x] = ("█", color)
        return canvas


def fit_frame_to_box(frame: List[str], max_w: int, max_h: int) -> List[str]:
    if not frame or max_w <= 0 or max_h <= 0:
        return []

    src_h = len(frame)
    src_w = max((len(line) for line in frame), default=0)
    if src_h == 0 or src_w == 0:
        return []

    padded = [line.ljust(src_w) for line in frame]

    scale_x = max(1.0, src_w / max_w)
    scale_y = max(1.0, src_h / max_h)
    scale = max(scale_x, scale_y)

    out_w = max(1, min(max_w, int(src_w / scale)))
    out_h = max(1, min(max_h, int(src_h / scale)))

    result = []
    for oy in range(out_h):
        sy = min(src_h - 1, int(oy * src_h / out_h))
        row_chars = []
        for ox in range(out_w):
            sx = min(src_w - 1, int(ox * src_w / out_w))
            row_chars.append(padded[sy][sx])
        result.append("".join(row_chars).rstrip())

    return result


class LeafBoardTUI:
    def __init__(self, animation_path: str = "ascii-frames.json"):
        self.monitor = SystemMonitor()
        self.animation = AsciiAnimation(animation_path)
        self.running = True
        self.command_buffer = ""
        self.output_lines: List[str] = ["Welcome to Leaf Board. Type 'help'."]
        self.last_stats_update = 0.0
        self.stats_interval = 0.20

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(1, 214, -1)
        curses.init_pair(2, 220, -1)
        curses.init_pair(3, 252, -1)
        curses.init_pair(4, 120, -1)
        curses.init_pair(5, 190, -1)
        curses.init_pair(6, 208, -1)
        curses.init_pair(7, 244, -1)
        curses.init_pair(8, 46, -1)
        curses.init_pair(9, 196, -1)

    def draw_text(self, win, y, x, text, color=3, bold=False):
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

    def rounded_box(self, win, y, x, h, w, title="", color=1):
        if h < 2 or w < 2:
            return
        try:
            win.addstr(y, x, "╭" + "─" * (w - 2) + "╮", curses.color_pair(color))
            for i in range(1, h - 1):
                win.addstr(y + i, x, "│", curses.color_pair(color))
                win.addstr(y + i, x + w - 1, "│", curses.color_pair(color))
            win.addstr(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", curses.color_pair(color))

            if title and w > len(title) + 4:
                title_text = f" {title} "
                tx = x + max(2, (w - len(title_text)) // 2)
                self.draw_text(win, y, tx, title_text, 2, True)
        except curses.error:
            pass

    def draw_animation_panel(self, win, y, x, h, w):
        self.rounded_box(win, y, x, h, w, " LEAF OS ", 1)

        frame = self.animation.current_frame()
        if not frame:
            return

        inner_y = y + 1
        inner_x = x + 2
        inner_h = h - 2
        inner_w = w - 4

        if inner_h < 4 or inner_w < 8:
            self.draw_text(win, y + 1, x + 2, "Panel too small", 9, True)
            return

        fitted = fit_frame_to_box(frame, inner_w, inner_h)
        if not fitted:
            return

        frame_h = len(fitted)
        frame_w = max((len(line) for line in fitted), default=0)

        start_y = inner_y + max(0, (inner_h - frame_h) // 2)
        start_x = inner_x + max(0, (inner_w - frame_w) // 2)

        for i, line in enumerate(fitted):
            self.draw_text(win, start_y + i, start_x, line, 8)

    def draw_stats_panel(self, win, y, x, h, w, cpu, ram):
        self.rounded_box(win, y, x, h, w, " SYSTEM ", 1)
        self.draw_text(win, y + 2, x + 3, f"CPU  {cpu:5.1f}%", 6 if cpu > 80 else 5 if cpu > 50 else 4, True)
        self.draw_text(win, y + 3, x + 3, f"RAM  {ram:5.1f}%", 6 if ram > 80 else 5 if ram > 50 else 4, True)
        self.draw_text(win, y + 2, x + w - 18, time.strftime("%H:%M:%S"), 7)
        self.draw_text(win, y + 3, x + w - 18, "LIVE", 8, True)

    def draw_graph_panel(self, win, y, x, h, w, title, data):
        self.rounded_box(win, y, x, h, w, title, 1)

        inner_h = h - 3
        inner_w = w - 4
        if inner_h < 2 or inner_w < 4:
            return

        canvas = GraphRenderer.render_area(data, inner_w, inner_h)

        for row_i, row in enumerate(canvas):
            for col_i, (ch, color) in enumerate(row):
                if ch != " ":
                    try:
                        win.addstr(y + 1 + row_i, x + 2 + col_i, ch, curses.color_pair(color))
                    except curses.error:
                        pass

        bars = GraphRenderer.render_bars(data, inner_w)
        self.draw_text(win, y + h - 2, x + 2, bars[:inner_w], 2)

    def draw_log_panel(self, win, y, x, h, w):
        self.rounded_box(win, y, x, h, w, " COMMAND ", 1)
        usable = h - 3
        lines = self.output_lines[-max(1, usable - 1):]

        for i, line in enumerate(lines[: max(0, usable - 1)]):
            self.draw_text(win, y + 1 + i, x + 2, line[: max(0, w - 4)], 3)

        prompt = "> " + self.command_buffer
        self.draw_text(win, y + h - 2, x + 2, prompt[: max(0, w - 4)], 2, True)

    def process_command(self, cmd: str):
        cmd = cmd.strip().lower()
        if not cmd:
            return

        if cmd == "help":
            self.output_lines.extend([
                "Commands:",
                "  help    - show commands",
                "  clear   - clear output",
                "  stats   - print current usage",
                "  reload  - reload ascii json",
                "  quit    - exit app",
            ])
        elif cmd == "clear":
            self.output_lines = ["Output cleared."]
        elif cmd == "stats":
            self.output_lines.append(f"CPU {self.monitor.last_cpu:.1f}% | RAM {self.monitor.last_ram:.1f}%")
        elif cmd == "reload":
            try:
                self.animation.load()
                self.output_lines.append(
                    f"Reloaded {len(self.animation.frames)} frames "
                    f"({self.animation.max_width}x{self.animation.max_height})."
                )
            except Exception as e:
                self.output_lines.append(f"Reload failed: {e}")
        elif cmd in ("quit", "exit"):
            self.running = False
        else:
            self.output_lines.append(f"Unknown command: {cmd}")

    def draw_too_small(self, stdscr, h, w):
        self.rounded_box(stdscr, 0, 0, h, w, " LEAF BOARD ", 1)
        self.draw_text(stdscr, 2, 3, "Terminal too small", 9, True)
        self.draw_text(stdscr, 4, 3, f"Current size: {w}x{h}", 3)
        self.draw_text(stdscr, 5, 3, "Need at least about 100x28", 3)
        self.draw_text(stdscr, 7, 3, "The leaf will auto-fit when enough space exists.", 2, True)
        stdscr.refresh()

    def draw(self, stdscr):
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        if h < 28 or w < 100:
            self.draw_too_small(stdscr, h, w)
            return

        now = time.monotonic()
        if now - self.last_stats_update >= self.stats_interval:
            cpu, ram = self.monitor.update()
            self.last_stats_update = now
        else:
            cpu, ram = self.monitor.last_cpu, self.monitor.last_ram

        self.animation.tick()

        self.rounded_box(stdscr, 0, 0, h, w, " LEAF BOARD ", 1)

        left_w = max(44, min(72, int(w * 0.38)))
        right_x = left_w + 1
        right_w = w - right_x - 1

        self.draw_animation_panel(stdscr, 1, 1, h - 9, left_w)
        self.draw_stats_panel(stdscr, 1, right_x, 6, right_w, cpu, ram)
        self.draw_graph_panel(stdscr, 7, right_x, 9, right_w, " CPU HISTORY ", self.monitor.cpu_history)
        self.draw_graph_panel(stdscr, 16, right_x, 9, right_w, " RAM HISTORY ", self.monitor.ram_history)
        self.draw_log_panel(stdscr, h - 8, 1, 7, w - 2)

        footer = "Enter submit  •  Backspace delete  •  q quit  •  reload animation"
        self.draw_text(stdscr, h - 1, max(2, (w - len(footer)) // 2), footer, 7)

        stdscr.refresh()

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        stdscr.timeout(33)
        self.init_colors()
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
                    self.process_command(self.command_buffer)
                    self.command_buffer = ""
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    self.command_buffer = self.command_buffer[:-1]
                elif 32 <= key <= 126:
                    _, width = stdscr.getmaxyx()
                    if len(self.command_buffer) < width - 8:
                        self.command_buffer += chr(key)
            except curses.error:
                pass


def main():
    curses.wrapper(LeafBoardTUI("ascii-frames.json").run)


if __name__ == "__main__":
    main()