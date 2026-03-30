import psutil
from collections import deque
from typing import Deque, Tuple


class SystemMonitor:
    def __init__(self, history_size: int = 180):
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
