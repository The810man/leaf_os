from typing import List, Optional, Tuple

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation
from pages.base_page import BasePage


def process_command(cmd: str, output_lines: List[str], monitor: SystemMonitor, 
                   animation: AsciiAnimation, pages: List[BasePage], 
                   current_page_index: int) -> Tuple[bool, int]:
    """
    Process a command and return (should_continue, new_page_index).
    """
    cmd = cmd.strip().lower()
    if not cmd:
        return True, current_page_index

    if cmd == "help":
        output_lines.extend([
            "Commands:",
            "  help          - show commands",
            "  clear         - clear output",
            "  stats         - print current usage",
            "  reload        - reload ascii json",
            "  pages         - list available pages",
            "  page <n>      - switch to page n",
            "  next          - go to next page",
            "  prev          - go to previous page",
            "  quit          - exit app",
            "",
            "Plant Commands (on Plant Status page):",
            "  1-3           - switch between plants",
            "  c             - create new plant",
            "  water         - water current plant",
            "  harvest       - harvest current plant",
            "  remove        - remove current plant",
        ])
    elif cmd == "clear":
        output_lines.clear()
        output_lines.append("Output cleared.")
    elif cmd == "stats":
        output_lines.append(f"CPU {monitor.last_cpu:.1f}% | RAM {monitor.last_ram:.1f}%")
    elif cmd == "reload":
        try:
            animation.load()
            output_lines.append(
                f"Reloaded {len(animation.frames)} frames "
                f"({animation.max_width}x{animation.max_height})."
            )
        except Exception as e:
            output_lines.append(f"Reload failed: {e}")
    elif cmd == "pages":
        output_lines.append("Available pages:")
        for i, page in enumerate(pages):
            marker = " <-- CURRENT" if i == current_page_index else ""
            output_lines.append(f"  {i}: {page.get_title()}{marker}")
    elif cmd.startswith("page "):
        try:
            page_num = int(cmd.split()[1])
            if 0 <= page_num < len(pages):
                output_lines.append(f"Switched to page {page_num}: {pages[page_num].get_title()}")
                return True, page_num
            else:
                output_lines.append(f"Invalid page number. Use 0-{len(pages)-1}")
        except (ValueError, IndexError):
            output_lines.append("Usage: page <number>")
    elif cmd == "next":
        new_index = (current_page_index + 1) % len(pages)
        output_lines.append(f"Switched to page {new_index}: {pages[new_index].get_title()}")
        return True, new_index
    elif cmd == "prev":
        new_index = (current_page_index - 1) % len(pages)
        output_lines.append(f"Switched to page {new_index}: {pages[new_index].get_title()}")
        return True, new_index
    elif cmd in ("quit", "exit"):
        return False, current_page_index
    else:
        output_lines.append(f"Unknown command: {cmd}")

    return True, current_page_index
