from abc import ABC, abstractmethod
from typing import List

from models.system_monitor import SystemMonitor
from models.ascii_animation import AsciiAnimation


class BasePage(ABC):
    """Base class for all TUI pages."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def draw(self, stdscr, y: int, x: int, h: int, w: int, 
             monitor: SystemMonitor, animation: AsciiAnimation):
        """Draw the page content."""
        pass

    @abstractmethod
    def get_title(self) -> str:
        """Get the page title for display."""
        pass
